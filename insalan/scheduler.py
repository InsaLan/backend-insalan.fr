from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
import logging

scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)

# Remove apscheduler logs
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)

def start():
    try:
        scheduler.start()
    except:
        pass  # Scheduler is already running