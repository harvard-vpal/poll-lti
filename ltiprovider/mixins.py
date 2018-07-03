from importlib import import_module
import logging
from urllib.parse import urlencode, urlparse, parse_qs

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from django.shortcuts import redirect
from lti import InvalidLTIRequestError
from lti.contrib.django import DjangoToolProvider
from oauthlib.oauth1 import OAuth1Error

from .models import LtiUser, LtiConsumer
from .outcomes import update_grade
from .validator import SignatureValidator


log = logging.getLogger(__name__)
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


class LtiMixin:
    """
    Mixin for LTI launch views
    Workflow:
    - LTI authentication
        - look up secret using consumer key
        - request verification
    - Get or create user based on (user_id, tool consumer instance id)
    Also supports environments where cookies are not able to be set, by putting session key in url
    """
    @csrf_exempt
    @xframe_options_exempt
    def dispatch(self, request, *args, **kwargs):
        # flow for initial LTI launch
        if request.method == 'POST' and request.POST.get('lti_message_type') == 'basic-lti-launch-request':
            # path to redirect to as GET request
            redirect_path = request.path
            if not request.session.session_key:
                request.session.create()
                log.debug("LTI Launch: Session key storage in cookie failed; created new session")
                # append session id to end of redirect path
                redirect_path = "{}?{}".format(redirect_path, urlencode({'session': request.session.session_key}))

            # store lti launch params in session before redirecting
            tool_provider = DjangoToolProvider.from_django_request(request=request)
            validate_lti_request(tool_provider)
            initialize_lti_session(request, tool_provider)

            # redirect to same view as get instead of post
            return redirect(redirect_path)

        # flow for all other LTI session activity
        else:
            # ensure session is set properly
            set_session(request)
            is_lti_session = check_if_lti_session(request)
            if not is_lti_session:
                log.error('LTI session is not found, Request cannot be processed')
                raise PermissionDenied("Content is available only through LTI protocol.")

            return super(LtiMixin, self).dispatch(request, *args, **kwargs)

    def get_lti_user(self):
        """
        Useful for getting the lti user object in a view
        :return: LtiUser model instance
        """
        return LtiUser.objects.get(user_id=self.request.session['user_id'])

    def is_graded(self):
        """
        Indicates whether the lti component is graded or ungraded, based on presence of lis_result_sourcedid param
        :return: bool, True if graded, False if not graded
        """
        return 'lis_result_sourcedid' in self.request.session

    def update_grade(self, score):
        """
        Updates the lti component grade in the LMS
        :param score: float, score between 0.0 and 1.0
        :return:
        """
        if not self.is_graded():
            log.warning('LMS grade update attempted on an ungraded LTI component')
        return update_grade(self.request.session, score)


def get_session_key(request):
    """
    Get the session key of the relevant current django session.
    If not available (due to cookie restrictions), the session key may located as:
        - "session" query parameter in request url
        - "session" query parameter in referring url
    :param request: django request object
    :return: str, session key
    """
    log.debug("Referring url: {}".format(request.META['HTTP_REFERER']))
    referring_url_params = parse_qs(urlparse(request.META['HTTP_REFERER']).query)
    if request.session.session_key:
        return request.session.session_key
    elif 'session' in request.GET:
        # get session by session key
        log.debug('Getting session key from url')
        return request.GET['session']
    # check if session is a query param in referring url
    elif 'session' in referring_url_params:
        log.debug("Getting session key from referring url")
        if 'session' in referring_url_params:
            return referring_url_params['session'][0]
    else:
        raise Http404('Session key not found')


def set_session(request):
    """
    Gets the session (either from request object or using info in url)
    :param request: django request object
    :return: None
    """
    session_key = get_session_key(request)
    log.debug("Setting session with key: {}".format(session_key))
    request.session = SessionStore(session_key)


def initialize_lti_session(request, tool_provider):
    """
    Store all LTI params in session and create LTI user object if necessary
    :param request: django request object
    :param tool_provider: lti.ToolProvider object
    :return: None
    """
    # store all LTI params in session
    for prop, value in tool_provider.to_params().items():
        request.session[prop] = value

    get_or_create_lti_user(tool_provider)


def check_if_lti_session(request):
    """
    Checks if request is part of a lti user session,
    by checking for presence of lti_message_type param in django session
    :param request: django request object
    :return:
    """
    return request.session.get('lti_message_type', False)


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
    except (OAuth1Error, InvalidLTIRequestError, ValueError) as err:
        is_valid_lti_request = False
        log.error('Error occurred during LTI request verification: {}'.format(err.__str__()))
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
