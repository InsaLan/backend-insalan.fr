"""This module contains the URL patterns for the ecological statistics app."""

from django.urls import path

from .views import CreateTravelData


app_name = "ecology"
urlpatterns = [
    path("travel-data/", CreateTravelData.as_view(), name="create-travel-data"),
]
