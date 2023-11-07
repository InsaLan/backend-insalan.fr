from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Module de gestion de contenu")
    name = "insalan.cms"
