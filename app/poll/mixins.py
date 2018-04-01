from lti_provider.mixins import LTIAuthMixin as BaseLTIAuthMixin


class LTIAuthMixin(BaseLTIAuthMixin):
    """
    Override dispatch method to support SSL termination
    With SSL termination at a load balancer, django receives request over http, but the url used for lti verification
    should be https. The mitodl/pylti looks for the 'X-Forwarded-Proto' header value
    (https://github.com/mitodl/pylti/blob/master/pylti/common.py#L279) but django changes header names in request.META
    to uppercase form (https://docs.djangoproject.com/en/2.0/ref/request-response/#django.http.HttpRequest.META)
    """

    def dispatch(self, request, *args, **kwargs):
        if request.META.get('HTTP_X_FORWARDED_PROTO') == 'https':
            request.META['X-Forwarded-Proto'] = 'https'

        return super().dispatch(request, *args, **kwargs)
