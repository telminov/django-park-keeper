# coding: utf-8
from django.core.management import BaseCommand

from parkkeeper import checker

class Command(BaseCommand):
    help = 'Start http checker cycle'

    def handle(self, *args, **options):
        checker.ShellChecker.start()
