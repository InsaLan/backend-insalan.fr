"""This module contains the configuration for the ecological statistics app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EcologyConfig(AppConfig):
    """Ecological statistics app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "insalan.ecology"
    verbose_name = _("Statistiques écologiques")
