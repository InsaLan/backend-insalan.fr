from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers import SchedulerAlreadyRunningError
from django.conf import settings
scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)

def start():
    try:
        scheduler.start()
    except SchedulerAlreadyRunningError:
        pass
