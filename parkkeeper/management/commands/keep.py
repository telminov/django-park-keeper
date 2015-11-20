# coding: utf-8
import asyncio
import signal

from django.core.management import BaseCommand
from parkkeeper.task_generator import TaskGenerator
from parkkeeper.task_result_collector import TaskResultCollector
from parkkeeper.event import EventProcessor
from parkkeeper.worker_processor import WorkerProcessor


class Command(BaseCommand):
    help = 'Start task generation and results collecting'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.event_processor = EventProcessor(verbose=True)
        self.task_generator = TaskGenerator(verbose=True)
        self.result_collector = TaskResultCollector(verbose=True)
        self.worker_processor = WorkerProcessor(verbose=True)

        signal.signal(signal.SIGINT, self.signal_handler)

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()

        try:
            loop.create_task(self.event_processor.process())
            loop.run_until_complete(
                asyncio.gather(
                    self.task_generator.generate_monit_tasks(),
                    self.task_generator.generate_work_tasks(),
                    self.task_generator.push_tasks(),
                    self.result_collector.collect_tasks(),
                    self.worker_processor.clear_dead_workers(),
                    self.worker_processor.register_workers(),
                    self.worker_processor.process_workers(),
                )
            )
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()

    def signal_handler(self, signal, frame):
        print('Stopping...')
        self.event_processor.stop()
        self.task_generator.stop()
        self.result_collector.stop()
        self.worker_processor.stop()
