# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.keeper import Sink

class Command(BaseCommand):
    help = 'Start main background keeper process for scheduling jobs'

    def handle(self, *args, **options):
        sink = Sink()
        sink.start()
