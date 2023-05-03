import os, ssl, multiprocessing

from celery import Celery
from celery.signals import worker_ready
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery("config")
proto = os.environ.get("CELERY_BROKER_PROTO")

class Config:
    beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'
    broker_url = (f'{str(os.environ.get("CELERY_BROKER_PROTO"))}://{str(os.environ.get("CELERY_BROKER_HOST"))}{os.environ.get("CELERY_BROKER_DB", "")}')
    result_backend = str(os.environ.get("CELERY_BROKER_BACK", None))
    broker_pool_limit = 10
    broker_connection_timeout = 30
    event_queue_expires = 60
    worker_concurrency = 5 * multiprocessing.cpu_count()
    worker_enable_remote_control = True
    worker_prefetch_multiplier = 1
    if proto == "redis":
        redis_max_connections = int(os.environ.get("CELERY_MAX_CONNECTIONS", 1))
    elif proto == "rediss":
        broker_use_ssl={'ssl_cert_reqs': ssl.CERT_REQUIRED}
        redis_backend_use_ssl={'ssl_cert_reqs': ssl.CERT_REQUIRED}
        redis_max_connections = int(os.environ.get("CELERY_MAX_CONNECTIONS", 1))
    elif proto == "amqp":
        broker_heartbeat = None
        result_backend = None
    elif proto == "amqps":
        broker_use_ssl={'cert_reqs': ssl.CERT_REQUIRED}
        broker_heartbeat = None
        result_backend = None

app.config_from_object(Config)
app.autodiscover_tasks(related_name='tasks')
app.autodiscover_tasks(related_name='peers')
app.autodiscover_tasks(related_name='other')
app.control.purge()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

def beat_schedule(self):
    app.conf.beat_schedule = {
        'runner-TxTotal': {
            'task': 'scan.tasks.runner_TxTotal',
            'schedule': crontab(minute='*/1'),
        },
        'runner-Exchange': {
            'task': 'scan.tasks.runner_Exchange',
            'schedule': crontab(minute='*/1'),
        },
        'runner-Circulating': {
            'task': 'scan.tasks.runner_Circulating',
            'schedule': crontab(minute='*/1'),
        },
        'runner-MasterSNR': {
            'task': 'scan.tasks.update_MasterSNR',  
            'schedule': crontab(minute=0, hour='*/6'),
        },
        'runner-PeerMonitor': {
            'task': 'scan.peers.peer_cmd',
            'schedule': crontab(minute='*/15'),
            'options': {'queue' : 'celery_peers'},
        },
        'runner-CheckOffline': {
            'task': 'scan.peers.check_offline',
            'schedule': crontab(minute='*/1'),
            'options': {'queue' : 'celery_peers'},
        }
    }
beat_schedule(app)

@worker_ready.connect
def at_start(sender, **k):
    with sender.app.connection() as conn:
        sender.app.send_task('scan.tasks.update_MasterSNR', connection=conn)
        sender.app.send_task('scan.peers.peer_cmd', connection=conn)

    for key in app.conf.beat_schedule.items():
        print(f"{key}")