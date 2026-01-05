import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_reminder.settings')

app = Celery('medicine_reminder')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')


# Optional: Configure additional Celery Beat schedules
app.conf.beat_schedule = {
    'send-dose-reminders-every-minute': {
        'task': 'apps.reminders.tasks.send_dose_reminders',
        'schedule': 60.0,  # Every 60 seconds
    },
    # Can add more scheduled tasks here
    # Example: Check for expiring medicines daily at 9 AM
    # 'check-expiring-medicines': {
    #     'task': 'apps.inventory.tasks.check_expiring_medicines',
    #     'schedule': crontab(hour=9, minute=0),
    # },
}

app.conf.timezone = 'UTC'