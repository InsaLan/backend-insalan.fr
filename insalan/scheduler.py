from apscheduler.schedulers.background import BackgroundScheduler # type: ignore[import]
from apscheduler.schedulers import SchedulerAlreadyRunningError # type: ignore[import]
from django.conf import settings
scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)

def start() -> None:
    try:
        scheduler.start()
    except SchedulerAlreadyRunningError:
        pass
