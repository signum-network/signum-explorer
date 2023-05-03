from django.core.management import BaseCommand
from celery import Celery, shared_task
from config.celery import app, beat_schedule

from django_celery_beat.models import PeriodicTask

class Command(BaseCommand):
    help = "Delete celery database ## WARNING EXPLORER RESTART REQUIRED ##"

    def handle(self, *args, **options):
        print(PeriodicTask.objects.all().delete())
        print("The explorer must be restarted now")