# coding: utf-8
from django.core.management import BaseCommand

import parkkeeper.ws

class Command(BaseCommand):
    help = 'Start aiohttp server'

    def handle(self, *args, **options):
        parkkeeper.ws.start_server()
