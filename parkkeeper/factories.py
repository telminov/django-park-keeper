# coding: utf-8
from django.conf import settings
import factory
import factory.fuzzy
from django.utils.timezone import now
from . import models


class WorkerType(factory.django.DjangoModelFactory):
    class Meta:
        model = models.WorkerType

    name = factory.fuzzy.FuzzyText(length=15, prefix='test_worker_')
    port = factory.fuzzy.FuzzyInteger(
        low=settings.ZMQ_EVENT_PUBLISHER_PORT+1,
        high=settings.ZMQ_EVENT_PUBLISHER_PORT+9
    )


class Monit(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Monit

    name = factory.fuzzy.FuzzyText(length=15, prefix='test_monit_')
    worker_type = factory.SubFactory(WorkerType)


class Work(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Work

    name = factory.fuzzy.FuzzyText(length=15, prefix='test_work_')
    worker_type = factory.SubFactory(WorkerType)


class Host(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Host

    name = factory.fuzzy.FuzzyText(length=15, prefix='test_host_')
    address = factory.Faker('ipv4')


class MonitSchedule(factory.django.DjangoModelFactory):
    class Meta:
        model = models.MonitSchedule

    monit = factory.SubFactory(Monit)


class Worker(factory.mongoengine.MongoEngineFactory):
    class Meta:
        model = models.Worker

    uuid = factory.Faker('uuid4')
    id = factory.Faker('uuid4')
    created_dt = now().replace(microsecond=0)
    host_name = factory.fuzzy.FuzzyText(length=5)
    type = factory.fuzzy.FuzzyText(length=5)


class Result(factory.mongoengine.MongoEngineFactory):
    class Meta:
        model = models.Result

    dt = now().replace(microsecond=0)
    extra = {'test': 'extra data'}
    level = factory.fuzzy.FuzzyInteger(low=1, high=3)


class MonitTask(factory.mongoengine.MongoEngineFactory):
    class Meta:
        model = models.MonitTask

    host_address = factory.Faker('ipv4')


class WorkTask(factory.mongoengine.MongoEngineFactory):
    class Meta:
        model = models.WorkTask

    host_address = factory.Faker('ipv4')


class CurrentWorker(factory.mongoengine.MongoEngineFactory):
    class Meta:
        model = models.CurrentWorker

    main = factory.SubFactory(Worker)
