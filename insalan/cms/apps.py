"""
Module for managing the CMS application.
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CmsConfig(AppConfig):
    """
    App configuration
    """
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Module de gestion de contenu")
    name = "insalan.cms"
