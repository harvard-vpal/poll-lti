from django.contrib import messages
from pylti.common import LTIPostMessageException, post_message
import time


def message_identifier():
    return '{:.0f}'.format(time.time())


def post_grade(score, request, lti):
    """
    Move LTI grade passback functionality from LTIPostGrade view to utility function for more flexibility
    https://github.com/ccnmtl/django-lti-provider/blob/master/lti_provider/views.py#L156
    """

    xml = lti.generate_request_xml(
        message_identifier(), 'replaceResult',
        lti.lis_result_sourcedid(request), score, None)

    if not post_message(
        lti.consumers(), lti.oauth_consumer_key(request),
            lti.lis_outcome_service_url(request), xml):

        msg = ('An error occurred while saving your score. '
               'Please try again.')
        messages.add_message(request, messages.ERROR, msg)

        # Something went wrong, display an error.
        # Is 500 the right thing to do here?
        raise LTIPostMessageException('Post grade failed')
    else:
        msg = ('Your score was submitted. Great job!')
        messages.add_message(request, messages.INFO, msg)
