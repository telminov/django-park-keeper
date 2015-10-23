# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.keeper import MonitWorker

class Command(BaseCommand):
    help = 'Start monitoring workers.'

    def add_arguments(self, parser):
        parser.add_argument('workers_count', type=int, help='Number of workers.', default=2, nargs='?')

    def handle(self, *args, **options):
        workers = []

        workers_count = options['workers_count']
        for i in range(0, workers_count):
            worker = MonitWorker()
            worker.setup(i)
            worker.start()
            workers.append(worker)

        for worker in workers:
            worker.join()
