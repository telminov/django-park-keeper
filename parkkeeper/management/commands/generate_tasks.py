# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.task_generator import TaskGenerator


class Command(BaseCommand):
    help = 'Start TaskGenerator'

    def handle(self, *args, **options):
        TaskGenerator().run()
