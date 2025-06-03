from django.urls import path
from apps.authentication_module.views import register

urlpatterns=[
    path('register/', register),
]