from django.core.management import BaseCommand
from celery import Celery, shared_task

from scan.peers import peer_cleanup

class Command(BaseCommand):
    help = "Manually delete old peers from the database"

    def handle(self, *args, **options):
        peer_cleanup.delay()