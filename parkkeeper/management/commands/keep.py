# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.keeper import MonitScheduler, MonitResultCollector

class Command(BaseCommand):
    help = 'Start main background keeper process for scheduling jobs'

    def handle(self, *args, **options):
        monit_scheduler = MonitScheduler()
        monit_scheduler.start()

        monit_result_collector = MonitResultCollector()
        monit_result_collector.start()

        for p in [monit_scheduler, monit_result_collector]:
            p.join()


