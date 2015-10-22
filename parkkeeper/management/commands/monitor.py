# coding: utf-8
from django.core.management import BaseCommand
from parkkeeper.monits.base import Monit
from parkkeeper import models

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
            task = models.MonitTask(
                monit_name=monit_name,
                host_address=host,
            )
            task.save()

            result = monit.check(host)
            task.result = result
            task.save()

            print(monit.name, task.host_address, ':', result.is_success)



