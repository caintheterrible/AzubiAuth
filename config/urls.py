from django.urls import path, include

from apps.authentication_module.urls import url_dispatch

urlpatterns=[
    path('', url_dispatch),
]