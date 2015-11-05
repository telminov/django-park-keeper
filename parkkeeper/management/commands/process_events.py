# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.event import EventProcessor


class Command(BaseCommand):
    help = 'Start EventProcessor'

    def handle(self, *args, **options):
        EventProcessor().run()
