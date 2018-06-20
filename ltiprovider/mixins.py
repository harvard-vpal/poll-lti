import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from lti import InvalidLTIRequestError
from lti.contrib.django import DjangoToolProvider
from oauthlib import oauth1

from .validator import SignatureValidator
from .models import LtiUser, LtiConsumer


log = logging.getLogger(__name__)


class LtiSessionMixin(object):
    """
    Mixin that enforces that user has an LTI session
    LTI session is indicated by the existence of the 'LTI_SESSION' session key/value
    """
    @xframe_options_exempt
    def dispatch(self, request, *args, **kwargs):
        lti_session = request.session.get('LTI_SESSION')
        if not lti_session:
            log.error('LTI session is not found, Request cannot be processed')
            raise PermissionDenied("Content is available only through LTI protocol.")
        return super(LtiSessionMixin, self).dispatch(request, *args, **kwargs)

    def get_lti_user(self, request):
        return LtiUser.objects.get(pk=request.session['LTI_USER_PK'])


class LtiLaunchMixin(LtiSessionMixin):
    """
    Mixin for LTI launch views
    Workflow:
    - LTI authentication
        - look up secret using consumer key
        - request verification
    - Get or create user based on (user_id, tool consumer instance id)
    """

    @csrf_exempt
    @xframe_options_exempt
    def dispatch(self, request, *args, **kwargs):
        tool_provider = DjangoToolProvider.from_django_request(request=request)
        validate_lti_request(tool_provider)
        lti_user, created = get_or_create_lti_user(tool_provider)
        store_lti_params_in_session(request.session, tool_provider)
        session['LTI_USER_PK'] = lti_user.pk
        session['LTI_SESSION'] = True
        return super(LtiLaunchMixin, self).dispatch(request, *args, **kwargs)


def store_lti_user_pk_in_session(session, lti_user):
    session['LTI_USER_PK'] = lti_user.pk


def check_if_lti_session(request):
    """
    Checks if request is part of a lti user session
    :param request: django request object
    :return:
    """
    return request.session.get('LTI_SESSION', False)


def store_lti_params_in_session(session, tool_provider):
    """
    Store LTI launch params in request session
    :param session: django request.session
    :param tool_provider: lti tool_provider object to get params from
    :return:
    """
    for prop, value in tool_provider.to_params().items():
        session[prop] = value


def validate_lti_request(tool_provider):
    """
    Check if LTI launch request is valid, and raise an exception if request is not valid
    An LTI launch is valid if:
    - The launch contains all the required parameters
    - The launch data is correctly signed using a known client key/secret pair
    :param tool_provider:
    :return: none
    """
    # if using reverse proxy, validate based on originating protocol
    # by replacing http with https in the url used for validation
    if tool_provider.launch_headers.get('HTTP_X_FORWARDED_PROTO') == 'https':
        tool_provider.launch_url = tool_provider.launch_url.replace('http:', 'https:', 1)

    validator = SignatureValidator()
    try:
        is_valid_lti_request = tool_provider.is_valid_request(validator)
    except (oauth1.OAuth1Error, InvalidLTIRequestError, ValueError) as err:
        is_valid_lti_request = False
        log.error('LTI request error: {}'.format(err.__str__()))
    if not is_valid_lti_request:
        raise Http404('LTI request is not valid')


def get_or_create_lti_user(tool_provider):
    """
    Get or create lti user based on lti launch params:
        'user_id',
        'oauth_consumer_key'
        'tool_consumer_instance_guid'
    Handle some cases where these request parameters are not found or invalid
    :return: (LtiUser model instance, bool)
    """
    user_id = tool_provider.launch_params.get('user_id')

    # get lti consumer model instance
    lti_consumer = LtiConsumer.objects.get(consumer_key=tool_provider.launch_params.get('oauth_consumer_key'))

    # tool consumer instance guid - set using default for lti consuumer if missing
    tool_consumer_instance_guid = tool_provider.launch_params.get('tool_consumer_instance_guid')
    if not tool_consumer_instance_guid:
        tool_consumer_instance_guid = lti_consumer.default_tool_consumer_instance_guid
        # TODO possibly infer a tool_consumer_instance_guid value based on request origin

    # get or create the lti user model instance
    lti_user, created = LtiUser.objects.get_or_create(
        user_id=user_id,
        lti_consumer=lti_consumer,
        tool_consumer_instance_guid=tool_consumer_instance_guid
    )
    return lti_user, created
