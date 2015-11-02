# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.event import EventProcessor
from parkkeeper.task_generator import TaskGenerator
from parkkeeper.worker_processor import WorkerProcessor


class Command(BaseCommand):
    help = 'Start main background keeper process for scheduling jobs'

    def handle(self, *args, **options):
        event_processor = EventProcessor()
        event_processor.start()

        worker_processor = WorkerProcessor()
        worker_processor.start()

        task_generator = TaskGenerator()
        task_generator.start()

        for p in [task_generator, event_processor, worker_processor]:
            p.join()


