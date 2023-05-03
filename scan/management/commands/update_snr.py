from django.core.management import BaseCommand
from celery import Celery, shared_task

from scan.tasks import update_MasterSNR

class Command(BaseCommand):
    help = "Manually update SNR database"

    def handle(self, *args, **options):
        update_MasterSNR.delay()