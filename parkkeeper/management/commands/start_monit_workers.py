# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.keeper import Worker

class Command(BaseCommand):
    help = 'Start main background keeper process for scheduling jobs'

    def handle(self, *args, **options):
        workers = []

        for i in [1, 2]:
            worker = Worker()
            worker.setup(i)
            worker.start()
            workers.append(worker)

        for worker in workers:
            worker.join()
