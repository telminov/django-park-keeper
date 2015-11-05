# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.worker_processor import WorkerProcessor


class Command(BaseCommand):
    help = 'Start WorkerProcessor'

    def handle(self, *args, **options):
        WorkerProcessor().run()
