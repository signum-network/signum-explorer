from django.core.management import BaseCommand
from celery import Celery, shared_task

from scan.peers import check_offline

class Command(BaseCommand):
    help = "Manually delete old peers from the database"

    def handle(self, *args, **options):
        check_offline.delay()