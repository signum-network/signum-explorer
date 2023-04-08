import os
from celery import Celery
from celery.signals import worker_ready
from celery.schedules import crontab
from django.conf import settings
from config.settings import (
    TASKS_SCAN_DELAY,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(related_name='tasks')
app.autodiscover_tasks(related_name='peers')

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
        'schedule': crontab(minute=0, hour='*/6'),
    },
    'runner-PeerMonitor': {
        'task': 'scan.peers.peer_cmd',
        'schedule': crontab(minute='*/15'),
    },
    'runner-CheckOffline': {
        'task': 'scan.peers.check_offline',
        'schedule': crontab(minute='*/1'),
    }
}

@worker_ready.connect
def at_start(sender, **k):
    with sender.app.connection() as conn:
        sender.app.send_task('scan.tasks.update_MasterSNR', connection=conn)
        sender.app.send_task('scan.peers.peer_cmd', connection=conn)