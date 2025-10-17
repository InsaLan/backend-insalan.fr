from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)

def start():
    try:
        scheduler.start()
    except:
        pass  # Scheduler is already running