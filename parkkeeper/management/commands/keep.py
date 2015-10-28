# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.event_publisher import EventPublisher
from parkkeeper.keeper import MonitScheduler


class Command(BaseCommand):
    help = 'Start main background keeper process for scheduling jobs'

    def handle(self, *args, **options):
        monit_scheduler = MonitScheduler()
        monit_scheduler.start()

        event_publisher = EventPublisher()
        event_publisher.start()

        for p in [monit_scheduler, event_publisher]:
            p.join()


