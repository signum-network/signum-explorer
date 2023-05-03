from django.core.management import BaseCommand
from celery import Celery, shared_task

from config.celery import debug_task

class Command(BaseCommand):
    help = "Test celery command"

    def handle(self, *args, **options):
        debug_task.delay()