import logging
from lti import OutcomeRequest
from .models import LtiConsumer


log = logging.getLogger(__name__)


def update_grade(params, score):
    """
    Update the lti consumer grade
    :param params: Usually a request.session; Should have keys oauth_consumer_key, lis_outcome_service_url, lis_result_sourcedid
    :param score: Score between 0.0 and 1.0
    :return: lms response
    """
    # check if component is graded, since this is a common lms configuration error
    if 'oauth_consumer_key' in params and 'lis_outcome_service_url' not in params:
        raise KeyError('lis_outcome_service_url not found in LTI params. Is the lti consumer component graded?')
    lti_consumer = LtiConsumer.objects.get(consumer_key=params['oauth_consumer_key'])
    lms_response = send_grade_update(
        lti_consumer.consumer_key,
        lti_consumer.consumer_secret,
        params['lis_outcome_service_url'],
        params['lis_result_sourcedid'],
        score
    )
    return lms_response


def send_grade_update(consumer_key, consumer_secret, lis_outcome_service_url, lis_result_sourcedid, score):
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

    return lms_response