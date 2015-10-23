# coding: utf-8
from django.core.management import BaseCommand
# from parkkeeper.keeper import Keeper
from parkkeeper.keeper import Replayer

class Command(BaseCommand):
    help = 'Start main background keeper process for scheduling jobs'

    def handle(self, *args, **options):
        replayer = Replayer(1)
        replayer.start()
        # keeper = Keeper()