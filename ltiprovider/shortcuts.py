from django.shortcuts import redirect, resolve_url
from urllib.parse import urlencode


def session_redirect(to, request, *args, **kwargs):
    """
    Wrapper around django.shortcuts.redirect() that stores the session key as the "session" url query/GET parameter
    Usage: requires additional request argument
    # TODO could support detection of other existing url query parameters, instead of assuming no preexisting params
    :param to: model, view name, or url (see redirect() 'to' argument)
    :param request: django request object
    :return: HttpResponseDirect
    """
    redirect_url = resolve_url(to, *args, **kwargs)
    # if request is not None:
    if 'session' in request.GET:
        redirect_url = "{}?{}".format(redirect_url, urlencode({'session': request.GET['session']}))
    return redirect(redirect_url, **kwargs)
