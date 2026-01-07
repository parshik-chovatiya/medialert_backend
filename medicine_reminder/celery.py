import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_reminder.settings')

app = Celery('medicine_reminder')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')


app.conf.beat_schedule = {
    'send-dose-reminders-every-minute': {
        'task': 'apps.reminders.tasks.send_dose_reminders',
        'schedule': 60.0,  # Every 60 seconds
    },

}

app.conf.timezone = 'UTC'