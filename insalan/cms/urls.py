"""
This module contains the URL patterns for the CMS (Content Management System) app.

It defines the URL patterns for various views that handle constant and content management.

URL Patterns:
- constant/ : List all constants
- constant/<str:name> : Fetch a specific constant by name
- content/ : List all content
- content/<str:section>/ : Fetch content for a specific section
"""
from django.urls import path
from . import views

urlpatterns = [
    path("constant/", views.ConstantList.as_view(), name="constant/list"),
    path("constant/<str:name>/", views.ConstantFetch.as_view(), name="constant/name"),
    path("content/", views.ContentList.as_view(), name="content/list"),
    path(
        "content/<str:name>/", views.ContentFetch.as_view(), name="content/section"
    ),
]
