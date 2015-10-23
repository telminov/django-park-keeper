# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.keeper import Broker

class Command(BaseCommand):
    help = 'Start main background keeper process for scheduling jobs'

    def handle(self, *args, **options):
        broker = Broker()
        broker.start()
