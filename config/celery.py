import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

from config.settings import (
    TASKS_SCAN_DELAY, 
    TASKS_SNR_DELAY,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

app.conf.beat_schedule = {
    'runner-TxTotal': {
        'task': 'scan.tasks.runner_TxTotal',
        'schedule': TASKS_SCAN_DELAY,
    },
    'runner-Exchange': {
        'task': 'scan.tasks.runner_Exchange',
        'schedule': TASKS_SCAN_DELAY,
    },
    'runner-Circulating': {
        'task': 'scan.tasks.runner_Circulating',
        'schedule': TASKS_SCAN_DELAY,
    },
    'runner-MasterSNR': {
        'task': 'scan.tasks.update_MasterSNR',  
        'schedule': TASKS_SNR_DELAY,
    },
}