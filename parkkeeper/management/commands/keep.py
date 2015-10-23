# coding: utf-8
from django.core.management import BaseCommand
# from parkkeeper.keeper import Keeper
from parkkeeper.keeper import Requester

class Command(BaseCommand):
    help = 'Start main background keeper process for scheduling jobs'

    def handle(self, *args, **options):
        requester = Requester()
        requester.start()
        # keeper = Keeper()
        # keeper.start_loop()



