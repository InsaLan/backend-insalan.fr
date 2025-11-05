"""App configuration"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from insalan.scheduler import scheduler
from django.utils import timezone
from datetime import timedelta
import logging
    
logger = logging.getLogger(__name__)

def check_ongoing_events() -> None:
    from .models import Event
    for event in Event.objects.filter(ongoing=True):
        now = timezone.now().date()
        if now == event.date_end + timedelta(weeks=1):
            event.ongoing = False
            event.save()
            logger.info(f"Switch ongoing to False for event {event.name}")


class TournamentConfig(AppConfig):
    """Tournament app config"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = "insalan.tournament"
    verbose_name = _("Tournois")

    def ready(self) -> None:
        """Called when the module is ready"""
        # pylint: disable-next=import-outside-toplevel
        from .payment import payment_handler_register

        payment_handler_register()
        
        scheduler.add_job(check_ongoing_events, 'interval', days=1)
