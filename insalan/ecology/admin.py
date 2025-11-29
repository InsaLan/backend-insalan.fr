"""
This module contains the admin configuration for the ecological statistics app.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin  # type: ignore[import]

from .models import TravelData


class TravelDataAdmin(ModelAdmin):  # type: ignore[misc]
    """Admin class for the TravelData model."""

    list_display = ("id", "city", "transportation_method", "event")
    search_fields = ("city",)
    list_filter = ("transportation_method", "event")


admin.site.register(TravelData, TravelDataAdmin)
