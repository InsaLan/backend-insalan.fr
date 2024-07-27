"""Pizza application"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class PizzaConfig(AppConfig):
    """Configuration of the Pizza App"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "insalan.pizza"
    verbose_name = _("Pizza")
