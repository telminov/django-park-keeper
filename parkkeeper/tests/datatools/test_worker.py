# coding: utf-8
import datetime
from unittest import mock

from django.test import TestCase
from django.utils.timezone import now
from djutils.testrunner import TearDownTestCaseMixin
from parkkeeper import models
from parkkeeper import factories
import parkkeeper.datatools.worker


class TaskTestCase(TearDownTestCaseMixin, TestCase):
    def setUp(self):
        self.worker = factories.Worker()

    def tearDown(self):
        self.tearDownMongo()

    def get_worker_data(self):
        return {
            'main': self.worker.to_mongo().to_dict(),
            'heart_beat_dt': now(),
        }

    def test_process_worker_new(self):
        self.assertFalse(models.CurrentWorker.objects.all().count())
        parkkeeper.datatools.worker.process_worker_data(self.get_worker_data())
        self.assertTrue(models.CurrentWorker.objects.filter(main=self.worker).count())

    def test_process_worker_stop(self):
        factories.CurrentWorker(main=self.worker)
        self.assertTrue(models.CurrentWorker.objects.filter(main=self.worker).count())

        worker_data = self.get_worker_data()
        worker_data['stop_dt'] = now()
        parkkeeper.datatools.worker.process_worker_data(worker_data)
        self.assertFalse(models.CurrentWorker.objects.all().count())

    def test_process_worker_monits(self):
        factories.CurrentWorker(main=self.worker)
        self.assertTrue(models.CurrentWorker.objects.filter(main=self.worker, monit_names=[]).count())

        worker_data = self.get_worker_data()
        worker_data['monits'] = {'test_monit1': 'description1', 'test_monit2': 'description2'}
        monit_names = ['test_monit1', 'test_monit2']
        parkkeeper.datatools.worker.process_worker_data(worker_data)
        self.assertTrue(models.CurrentWorker.objects.filter(main=self.worker, monit_names=monit_names).count())

    def test_process_worker_works(self):
        factories.CurrentWorker(main=self.worker)
        self.assertTrue(models.CurrentWorker.objects.filter(main=self.worker, work_names=[]).count())

        worker_data = self.get_worker_data()
        worker_data['works'] = {'test_work1': 'description1', 'test_work2': 'description2'}
        work_names = ['test_work1', 'test_work2']
        parkkeeper.datatools.worker.process_worker_data(worker_data)
        self.assertTrue(models.CurrentWorker.objects.filter(main=self.worker, work_names=work_names).count())
