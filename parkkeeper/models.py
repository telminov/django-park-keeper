# coding: utf-8
import json
from typing import Set, Dict, List

import datetime

from bson import json_util
from django.conf import settings
from django.db.models import Max
from django.db import models
from django.utils.timezone import now, make_aware
import mongoengine
from croniter import croniter
from mongoengine.connection import get_db
from swutils.encrypt import encrypt, decrypt
from parkworker.const import LEVEL_CHOICES, TASK_TYPE_MONIT, TASK_TYPE_WORK


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
    port = models.IntegerField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    @classmethod
    def create_if_not_exists(cls, name) -> 'WorkerType':
        # TODO: make more atomic
        max_port = cls.objects.aggregate(max_port=Max('port'))['max_port'] or 5550
        worker_type, _ = cls.objects.get_or_create(name=name, defaults={'port': max_port+1})
        return worker_type

    # def get_waiting_monit_tasks(self):
    #     monit_tasks = []
    #     for monit in self.monits.all():
    #         waiting_monit_tasks = MonitTask.objects.filter(monit_name=monit.name, start_dt=None)
    #         monit_tasks.extend(waiting_monit_tasks)
    #     return monit_tasks
    #
    # def get_waiting_work_tasks(self):
    #     work_tasks = []
    #     for work in self.works.all():
    #         waiting_monit_tasks = WorkTask.objects.filter(work_name=work.name, start_dt=None)
    #         work_tasks.extend(waiting_monit_tasks)
    #     return work_tasks


class Monit(models.Model):
    name = models.CharField(max_length=255, unique=True)
    worker_type = models.ForeignKey(WorkerType, related_name='monits')
    description = models.TextField()

    def __str__(self):
        return self.name

    def get_current_workers(self):
        return CurrentWorker.objects.filter(monit_names=self.name)

    @ classmethod
    def create_if_not_exists(cls, worker_type: WorkerType, monits: dict):
        """
        create not exists in db worker monits
        """
        for monit_name, description in monits.items():
            if not cls.objects.filter(name=monit_name).exists():
                cls.objects.create(
                    name=monit_name,
                    worker_type=worker_type,
                    description=description,
                )


class Work(models.Model):
    name = models.CharField(max_length=255, unique=True)
    worker_type = models.ForeignKey(WorkerType, related_name='works')
    description = models.TextField()

    def __str__(self):
        return self.name

    def get_current_workers(self):
        return CurrentWorker.objects.filter(work_names=self.name)

    @ classmethod
    def create_if_not_exists(cls, worker_type: WorkerType, works: dict):
        """
        create not exists in db worker works
        """
        for work_name, description in works.items():
            if not cls.objects.filter(name=work_name).exists():
                cls.objects.create(
                    name=work_name,
                    worker_type=worker_type,
                    description=description,
                )


class NoCronException(Exception): pass


class Schedule(models.Model):
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

    options_json = models.TextField(blank=True, help_text='kwargs in json format for task')

    count = models.IntegerField(default=1, null=True, blank=True)
    interval = models.IntegerField(default=1, null=True, blank=True)
    time_units = models.CharField(max_length=50, choices=TIME_UNIT_CHOICES, default=MINUTE_UNIT)
    period = models.IntegerField(editable=False, help_text='in seconds', null=True)

    cron = models.CharField(max_length=50, verbose_name='Cron-style schedule', help_text='* * * * *',
                            default='', blank=True)

    hosts = models.ManyToManyField(Host, blank=True)
    groups = models.ManyToManyField(HostGroup, blank=True)
    credential_types = models.ManyToManyField(CredentialType, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.period = self._get_period()
        super().save(*args, **kwargs)

    def get_options(self) -> dict:
        if self.options_json:
            return json.loads(self.options_json)
        else:
            return {}

    def get_credentials(self, host):
        credentials = {}
        for credential_type in self.credential_types.all():
            host_credential_qs = HostCredential.objects.filter(host=host, credential__type=credential_type)
            if host_credential_qs:
                credential = host_credential_qs[0].credential
                credentials[credential_type.name] = {
                    'username': credential.username,
                    'encrypted_password': credential.encrypted_password,
                }
        return credentials

    def get_hosts(self) -> Set[Host]:
        """ hosts for applying tasks """
        hosts = set(self.hosts.all())
        for group in self.groups.all():
            hosts.update(group.hosts.all())
        return hosts

    def get_next_cron_dt(self, from_dt: datetime.datetime):
        if not self.cron:
            raise NoCronException('Schedule %s with id %s have no cron schedule.' % (type(self), self.id))

        cron_iter = croniter(self.cron, from_dt)
        next_dt = cron_iter.get_next(datetime.datetime)
        return next_dt

    def init_task(self):
        raise NotImplemented()

    @staticmethod
    def get_task_collection():
        raise NotImplemented()
        
    @classmethod
    def get_latest_results(cls) -> Dict[int, dict]:
        result = cls.get_task_collection().aggregate(pipeline=[
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
    def get_need_to_create(cls) -> List['Schedule']:
        schedules = []

        latest_results = cls.get_latest_results()
        for schedule in cls.objects.filter(is_active=True):
            need_to_create = False

            # results exists, check result time
            if schedule.id in latest_results:
                latest_dc = latest_results[schedule.id]['latest_dc']
                delta = now() - latest_dc
                secs_from_last_task = delta.seconds

                if schedule.cron:
                    if now() >= schedule.get_next_cron_dt(latest_dc):
                        need_to_create = True
                elif schedule.period:
                    if secs_from_last_task >= schedule.period:
                        need_to_create = True

            else:
                # not results before
                need_to_create = True

            if need_to_create:
                schedules.append(schedule)

        return schedules

    @classmethod
    def create_tasks(cls) -> List['BaseTask']:
        tasks = []
        for schedule in cls.get_need_to_create():
            for host in schedule.get_hosts():
                task = schedule.init_task()
                task.host_address = host.address
                task.options = schedule.get_options()

                # extend options by credentials
                credentials = schedule.get_credentials(host=host)
                if credentials:
                    task.options['credentials'] = schedule.get_credentials(host=host)

                task.save()
                tasks.append(task)

        return tasks

    def _get_period(self) -> int:
        """ count of seconds between tow checks """
        if self.interval and self.count and self.time_units:
            sec = self._get_seconds_in_unit()
            interval = (self.interval / self.count) * sec
            return interval
        else:
            return None

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


class MonitSchedule(Schedule):
    monit = models.ForeignKey(Monit)

    def __str__(self):
        return self.name or self.monit.name

    def init_task(self):
        return MonitTask(
            monit_name=self.monit.name,
            schedule_id=self.id
        )

    @staticmethod
    def get_task_collection():
        return get_db().monit_task


class WorkSchedule(Schedule):
    work = models.ForeignKey(Work)

    def __str__(self):
        return self.name or self.work.name

    def init_task(self):
        return WorkTask(
            work_name=self.work.name,
            schedule_id=self.id
        )

    @staticmethod
    def get_task_collection():
        return get_db().work_task


class Result(mongoengine.EmbeddedDocument):
    level = mongoengine.IntField(choices=LEVEL_CHOICES)
    extra = mongoengine.DictField()
    dt = mongoengine.DateTimeField(help_text='date and time of result')

    def get_data(self):
        data = self.to_mongo().to_dict()
        data['dt'] = data['dt'].replace(microsecond=0)
        return data


class Worker(mongoengine.EmbeddedDocument):
    uuid = mongoengine.UUIDField()
    id = mongoengine.StringField()
    created_dt = mongoengine.DateTimeField()
    host_name = mongoengine.StringField()
    type = mongoengine.StringField()

    def get_data(self):
        data = self.to_mongo().to_dict()
        data['created_dt'] = data['created_dt'].replace(microsecond=0)
        return data


class BaseTask(mongoengine.Document):
    host_address = mongoengine.StringField()
    options = mongoengine.DictField()

    schedule_id = mongoengine.IntField(null=True)

    dc = mongoengine.DateTimeField(verbose_name='Date and time of task creating')
    cancel_dt = mongoengine.DateTimeField(help_text='for task canceling', null=True)
    cancel_reason = mongoengine.StringField()

    worker = mongoengine.EmbeddedDocumentField(Worker, null=True)
    start_dt = mongoengine.DateTimeField(null=True)
    result = mongoengine.EmbeddedDocumentField(Result, null=True)

    def save(self, *args, **kwargs):
        if not self.dc:
            self.dc = now()
        super().save(*args, **kwargs)

    @classmethod
    def get_waiting_tasks(cls) -> mongoengine.QuerySet:
        return cls.objects.filter(
            cancel_dt=None,
            start_dt=None,
        )

    @classmethod
    def get_started_tasks(cls) -> mongoengine.QuerySet:
        return cls.objects.filter(
            cancel_dt=None,
            start_dt__ne=None,
            result__dt=None,
        )

    @classmethod
    def cancel_not_started(cls, reason, task_pk=None):
        params = {
            'start_dt': None,
        }
        if task_pk is not None:
            params['pk'] = task_pk

        cls.objects\
            .filter(**params)\
            .update(cancel_dt=now(), cancel_reason=reason)

    def get_name(self) -> str:
        raise NotImplemented()

    def get_worker_type(self) -> WorkerType:
        raise NotImplemented()

    def get_task_type(self) -> str:
        raise NotImplemented()

    def get_data(self) -> dict:
        task_data = self.to_mongo().to_dict()
        task_data['id'] = str(task_data.pop('_id'))
        task_data['dc'] = task_data['dc'].replace(microsecond=0)
        if task_data.get('start_dt'):
            task_data['start_dt'] = task_data['start_dt'].replace(microsecond=0)
        data = {
            'task': task_data,
            'type': self.get_task_type(),
        }
        return data

    def get_json(self) -> str:
        data = self.get_data()
        task_json = json.dumps(data, default=json_util.default)
        return task_json

    @staticmethod
    def get_task_model(task_type: str):
        if task_type == TASK_TYPE_MONIT:
            return MonitTask
        elif task_type == TASK_TYPE_WORK:
            return WorkTask
        else:
            raise Exception('Unknown task type "%s"' % task_type)

    meta = {
        'abstract': True
    }


class MonitTask(BaseTask):
    monit_name = mongoengine.StringField()

    def get_name(self) -> str:
        return self.monit_name

    def get_worker_type(self) -> WorkerType:
        return Monit.objects.get(name=self.monit_name).worker_type

    def get_task_type(self) -> str:
        return TASK_TYPE_MONIT


class WorkTask(BaseTask):
    work_name = mongoengine.StringField()

    def get_name(self) -> str:
        return self.work_name

    def get_worker_type(self) -> WorkerType:
        return Work.objects.get(name=self.work_name).worker_type

    def get_task_type(self) -> str:
        return TASK_TYPE_WORK


class CurrentWorker(mongoengine.Document):
    main = mongoengine.EmbeddedDocumentField(Worker)
    task_ids = mongoengine.ListField(mongoengine.ObjectIdField())
    monit_names = mongoengine.ListField(mongoengine.StringField())
    work_names = mongoengine.ListField(mongoengine.StringField())
    heart_beat_dt = mongoengine.DateTimeField()

    def get_tasks(self) -> List[MonitTask]:
        return MonitTask.objects.filter(id__in=self.task_ids)


from parkkeeper import signals