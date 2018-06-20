import hashlib
import logging

from django.conf import settings
import shortuuid
from lti import OutcomeRequest


log = logging.getLogger(__name__)


def short_token():
    """Generate a 20-character random token"""
    hash = hashlib.sha1(shortuuid.uuid().encode('utf-8'))
    hash.update(settings.SECRET_KEY.encode('utf-8'))
    return hash.hexdigest()[::2]


def infer_tool_consumer_instance_guid(request):
    """
    Use this when tool_consumer_instance_guid is not provided in lti launch
    Could try to detect the request origin domain and use that as the tool_consumer_instance guid
    """
    return NotImplementedError


def update_lti_consumer_grade(consumer_key, consumer_secret, lis_outcome_service_url, lis_result_sourcedid, score):
    """
    Send lms grade for an lti component
    :param consumer_key: lti client key
    :param consumer_secret: lti client secret
    :param lis_outcome_service_url: outcome service url to send outcome request to
    :param lis_result_sourcedid: context identifier for consumer to use
    :param score: score between 0.0 and 1.0
    :return:
    """
    outcome_request = OutcomeRequest()
    outcome_request.consumer_key = consumer_key
    outcome_request.consumer_secret = consumer_secret
    outcome_request.lis_outcome_service_url = lis_outcome_service_url
    outcome_request.lis_result_sourcedid = lis_result_sourcedid

    # construct info string for logging
    args = "score={}, lis_outcome_service_url={} lis_result_sourcedid={}, consumer_key={}, consumer_secret={}, ".format(
        score, lis_outcome_service_url, lis_result_sourcedid, consumer_key, consumer_secret
    )

    log.debug("Updating LMS grade, with parameters: {}".format(args))

    # send request to update score
    outcome_request.post_replace_result(score)

    # check out the request response
    lms_response = outcome_request.outcome_response

    # logging
    if lms_response.is_success():
        log.info("Successfully sent updated grade to LMS. {}".format(args))
    elif lms_response.is_processing():
        log.info("Grade update is being processed by LMS. {}, comment: {}".format(args, 'processing'))
    elif lms_response.has_warning():
        log.warning("Grade update response has warnings. {}, comment={}".format(args, 'processing'))
    else:
        log.error("Grade update request failed. {}, comment={}".format(args, lms_response.code_major))
