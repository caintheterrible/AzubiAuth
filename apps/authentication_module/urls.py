from django.urls import path
import re
from django.http import Http404
from apps.authentication_module.views import RegistrationView


class URLPattern:
    """URL pattern customization with regex validation."""
    def __init__(self, pattern, view, name=None):
        self.pattern= re.compile(pattern)
        self.view=view
        self.name=name

    def resolve(self, urlpath):
        match=self.pattern.match(urlpath)
        if match:
            return self.view, match.groups(), match.groupdict()
        return None

# URL dispatcher
def url_dispatch(request):
    patterns:list=[
        URLPattern(r'^api/register/?$', RegistrationView.as_view(), 'register'),
    ] # TO-DO: this can fetch from an external json file

    for pattern in patterns:
        result=pattern.resolve(request.path_info)
        if result:
            view, args, kwargs= result
            return view(request, *args, **kwargs)

    raise Http404("URL not found!")