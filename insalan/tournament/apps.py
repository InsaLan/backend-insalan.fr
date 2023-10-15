"""App configuration"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class TournamentConfig(AppConfig):
    """Tournament app config"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = "insalan.tournament"
    verbose_name = _("Tournois")

    def ready(self):
        """Called when the module is ready"""
        from .payment import payment_handler_register

        payment_handler_register()
