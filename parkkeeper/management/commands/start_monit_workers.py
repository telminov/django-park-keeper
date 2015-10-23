# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.keeper import Replayer

class Command(BaseCommand):
    help = 'Start main background keeper process for scheduling jobs'

    def handle(self, *args, **options):
        replayers = []

        for i in [1, 2]:
            replayer = Replayer()
            replayer.setup(i)
            replayer.start()
            replayers.append(replayer)

        for replayer in replayers:
            replayer.join()
