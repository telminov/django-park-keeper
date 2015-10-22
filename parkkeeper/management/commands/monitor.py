# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.monits.base import Monit

class Command(BaseCommand):
    help = 'Run monitoring checks manually'

    def add_arguments(self, parser):
        parser.add_argument('monit_name', type=str, help='Monitoring name. For example: general.ping')
        parser.add_argument('hosts', nargs='+', type=str, help='Hosts for monitoring')

    def handle(self, *args, **options):
        monit_name = options['monit_name']
        hosts = options['hosts']

        monit = Monit.get_monit(monit_name)()
        for host in hosts:
            result = monit.check(host)
            print(monit.name, result.host, ':', result.success)

