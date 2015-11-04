# coding: utf-8
import json
from typing import Set, Dict, List

from django.conf import settings
from django.db.models import Max
from django.db import models
from django.utils.timezone import now, make_aware
import mongoengine
from mongoengine.connection import get_db

from swutils.encrypt import encrypt, decrypt
from parkworker.const import LEVEL_CHOICES

class CredentialType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Credential(models.Model):
    name = models.CharField(max_length=255, unique=True)
    type = models.ForeignKey(CredentialType)
    username = models.CharField(max_length=100)
    encrypted_password = models.TextField()

    def __str__(self):
        return self.name

    def set_password(self, plain_password, save=True):
        self.encrypted_password = encrypt(plain_password, settings.SECRET_KEY.encode('utf-8'))
        if save:
            self.save()
        return self.encrypted_password

    def get_password(self):
        return decrypt(self.encrypted_password, settings.SECRET_KEY.encode('utf-8'))


class Host(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class HostCredential(models.Model):
    host = models.ForeignKey(Host)
    credential = models.ForeignKey(Credential)

    class Meta:
        unique_together = ('host', 'credential')

    def __str__(self):
        return '%s - %s' % (self.host, self.credential.name)


class HostGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    hosts = models.ManyToManyField(Host, related_name='groups')

    def __str__(self):
        return self.name


class WorkerType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    port = models.IntegerField()
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    @classmethod
    def create_if_not_exists(cls, name):
        # TODO: make more atomic
        max_port = cls.objects.aggregate(max_port=Max('port'))['max_port'] or 5550
        worker_type, _ = cls.objects.get_or_create(name=name, defaults={'port': max_port+1})
        return worker_type

class Monit(models.Model):
    name = models.CharField(max_length=255, unique=True)
    worker_type = models.ForeignKey(WorkerType)

    def __str__(self):
        return self.name

    def get_current_workers(self):
        return CurrentWorker.objects.filter(monit_names=self.name)


class MonitSchedule(models.Model):
    SEC_UNIT = 'seconds'
    MINUTE_UNIT = 'minutes'
    HOUR_UNIT = 'hours'
    DAY_UNIT = 'days'
    TIME_UNIT_CHOICES = (
        (SEC_UNIT, SEC_UNIT),
        (MINUTE_UNIT, MINUTE_UNIT),
        (HOUR_UNIT, HOUR_UNIT),
        (DAY_UNIT, DAY_UNIT),
    )
    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    monit = models.ForeignKey(Monit)
    options_json = models.TextField(blank=True, help_text='kwargs in json format for monitoring check')

    count = models.IntegerField(default=1)
    interval = models.IntegerField(default=1)
    time_units = models.CharField(max_length=50, choices=TIME_UNIT_CHOICES, default=MINUTE_UNIT)
    period = models.IntegerField(editable=False, help_text='in seconds')

    hosts = models.ManyToManyField(Host, blank=True)
    groups = models.ManyToManyField(HostGroup, blank=True)
    credential_types = models.ManyToManyField(CredentialType, blank=True)

    is_active = models.BooleanField(default=True)

    @staticmethod
    def get_latest_results() -> Dict[int, dict]:
        result = get_db().monit_task.aggregate(pipeline=[
            {
                '$match': {'$or': [{'cancel_dt': None}, {'cancel_dt': {'$exists': False}}]}
            },
            {
                '$group': {
                    '_id': '$schedule_id',
                    'latest_dc': {'$last': '$dc'},
                    'latest_result_dt': {'$last': '$result.dt'},
                    'latest_level': {'$last': '$result.level'},
                }
            },
            {
                '$project': {
                    'latest_result_dt': 1, 'latest_level': 1,  'latest_dc': 1, 'schedule_id': '$_id', '_id': 0
                }
            }
        ])

        latest_results = {}
        for item in result:
            schedule_id = item['schedule_id']
            latest_results[schedule_id] = item

        return latest_results

    @classmethod
    def create_tasks(cls) -> List['MonitTask']:
        """  """
        latest_results = cls.get_latest_results()

        monit_tasks = []
        for schedule in cls.objects.filter(is_active=True):
            if schedule.id in latest_results:
                latest_dc = latest_results[schedule.id]['latest_dc']
                delta = now() - make_aware(latest_dc)
                secs_from_last_task = delta.seconds
                need_to_create = secs_from_last_task >= schedule.period
            else:
                # tasks did not exists before
                need_to_create = True

            if need_to_create:
                for host in schedule.get_hosts():
                    task = MonitTask(
                        monit_name=schedule.monit.name,
                        host_address=host.address,
                        schedule_id=schedule.id,
                    )

                    options = schedule.get_options()
                    # extend options by credentials
                    for credential_type in schedule.credential_types.all():
                        host_credential_qs = HostCredential.objects.filter(host=host, credential__type=credential_type)
                        if host_credential_qs:
                            credential = host_credential_qs[0].credential
                            options.setdefault('credentials', {})[credential_type.name] = {
                                'username': credential.username,
                                'encrypted_password': credential.encrypted_password,
                            }
                    task.options = options

                    task.save()
                    monit_tasks.append(task)

        return monit_tasks

    def __str__(self):
        return self.name or self.monit.name

    def save(self, *args, **kwargs):
        self.period = self._get_period()
        super().save(*args, **kwargs)

    def get_hosts(self) -> Set[Host]:
        """ hosts for applying monitoring check """
        hosts = set(self.hosts.all())
        for group in self.groups.all():
            hosts.update(group.hosts.all())
        return hosts

    def get_options(self) -> dict:
        if self.options_json:
            return json.loads(self.options_json)
        else:
            return {}

    def _get_period(self) -> int:
        """ count of seconds between tow checks """
        sec = self._get_seconds_in_unit()
        interval = (self.interval / self.count) * sec
        return interval

    def _get_seconds_in_unit(self) -> int:
        if self.time_units == self.SEC_UNIT:
            sec = 1
        elif self.time_units == self.MINUTE_UNIT:
            sec = 60
        elif self.time_units == self.HOUR_UNIT:
            sec = 60 * 60
        elif self.time_units == self.DAY_UNIT:
            sec = 60 * 60 * 24
        else:
            raise Exception('Unexpected time unit "%s"' % self.time_units)
        return sec


class CheckResult(mongoengine.EmbeddedDocument):
    level = mongoengine.IntField(choices=LEVEL_CHOICES)
    extra = mongoengine.DictField()
    dt = mongoengine.DateTimeField(help_text='date and time of result')


class Worker(mongoengine.EmbeddedDocument):
    uuid = mongoengine.UUIDField()
    id = mongoengine.StringField()
    created_dt = mongoengine.DateTimeField()
    host_name = mongoengine.StringField()
    type = mongoengine.StringField()


class MonitTask(mongoengine.Document):
    monit_name = mongoengine.StringField()
    host_address = mongoengine.StringField()
    options = mongoengine.DictField()

    schedule_id = mongoengine.IntField(null=True)

    dc = mongoengine.DateTimeField(verbose_name='Date and time of task creating')
    cancel_dt = mongoengine.DateTimeField(help_text='for task canceling', null=True)
    cancel_reason = mongoengine.StringField()

    worker = mongoengine.EmbeddedDocumentField(Worker, null=True)
    start_dt = mongoengine.DateTimeField(null=True)
    result = mongoengine.EmbeddedDocumentField(CheckResult, null=True)

    def save(self, *args, **kwargs):
        if not self.dc:
            self.dc = now()
        super().save(*args, **kwargs)

    @classmethod
    def get_waiting_tasks(cls):
        return cls.objects.filter(
            cancel_dt=None,
            start_dt=None,
        )

    @classmethod
    def get_started_tasks(cls):
        return cls.objects.filter(
            cancel_dt=None,
            start_dt__ne=None,
            result__dt=None,
        )


class CurrentWorker(mongoengine.Document):
    main = mongoengine.EmbeddedDocumentField(Worker)
    task_ids = mongoengine.ListField(mongoengine.ObjectIdField())
    monit_names = mongoengine.ListField(mongoengine.StringField())
    heart_beat_dt = mongoengine.DateTimeField()

    def get_tasks(self):
        return MonitTask.objects.filter(id__in=self.task_ids)
