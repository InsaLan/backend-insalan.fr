"""
This module contains the configuration for the Tickets app.
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TicketsConfig(AppConfig):
    """
    App configuration
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "insalan.tickets"
    verbose_name = _("Tickets")
