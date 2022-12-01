from django.core.management import BaseCommand

from scan.tasks import task_cmd


class Command(BaseCommand):
    help = "Tasks"

    def handle(self, *args, **options):
        task_cmd()
