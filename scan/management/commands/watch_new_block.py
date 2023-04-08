import sys
from time import sleep

from django.core.management import BaseCommand

from scan.caching_data.last_height import CachingLastHeight
from scan.caching_data.last_difficulty import CachingCumulativeDifficulty

UP = "\x1B[2A"
CLR = "\x1B[0K"

class Command(BaseCommand):
    help = "Watch new block"

    def handle(self, *args, **options):
        print("\n\n")
        last_height = 0
        last_difficulty = 0
        while True:
            height = CachingLastHeight().live_data
            difficulty = CachingCumulativeDifficulty().live_data
            if last_height != height or last_difficulty != difficulty:
                last_height = height
                last_difficulty = difficulty
                CachingLastHeight().update_data(height)
                CachingCumulativeDifficulty().update_data(difficulty)
                print(f"""{UP}New block: {height}{CLR}\nNew CumulativeDifficulty: {difficulty}{CLR}\n""", end='', flush=True)
            sleep(1)
