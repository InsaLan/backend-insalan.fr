"""Partner application"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class PartnerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "insalan.partner"
    verbose_name = _("Partenaires & Sponsors")
