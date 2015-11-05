# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.task_result_collector import TaskResultCollector


class Command(BaseCommand):
    help = 'Start TaskResultCollector'

    def handle(self, *args, **options):
        TaskResultCollector().run()
