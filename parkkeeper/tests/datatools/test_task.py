# coding: utf-8
import datetime
from unittest import mock

from django.test import TestCase
from django.utils.timezone import now
from djutils.testrunner import TearDownTestCaseMixin
from parkkeeper import models
from parkkeeper import factories
from parkworker.const import EXISTS_MORE_LATE_TASK_CANCEL_REASON, WORKER_DEAD_CANCEL_REASON
import parkkeeper.datatools.task


class TaskTestCase(TearDownTestCaseMixin, TestCase):
    def setUp(self):
        monit = factories.Monit()
        self.monit_task = factories.MonitTask(monit_name=monit.name)

    def tearDown(self):
        self.tearDownMongo()

    def test_cancel_double(self):
        monit_task1 = factories.MonitTask(dc=now() - datetime.timedelta(seconds=10))
        monit_task2 = factories.MonitTask(dc=now(), host_address=monit_task1.host_address, options=monit_task1.options)

        last_data = monit_task2.get_data()
        parkkeeper.datatools.task.cancel_double(last_data['task'], last_data['type'])

        monit_task1 = models.MonitTask.objects.get(pk=monit_task1.pk)
        self.assertTrue(monit_task1.cancel_dt)
        self.assertEqual(monit_task1.cancel_reason, EXISTS_MORE_LATE_TASK_CANCEL_REASON)


    def test_process_task_no_new_data(self):
        data_before = self.monit_task.get_data()

        parkkeeper.datatools.task.process_task_data(data_before)

        task = models.MonitTask.objects.get(pk=self.monit_task.pk)
        data_after = task.get_data()

        self.assertEqual(
            data_before,
            data_after
        )

    def test_process_task_start_dt(self):
        data_before = self.monit_task.get_data()
        data_before['task']['start_dt'] = now().replace(microsecond=0)

        parkkeeper.datatools.task.process_task_data(data_before)

        task = models.MonitTask.objects.get(pk=self.monit_task.pk)
        data_after = task.get_data()

        self.assertEqual(
            data_before,
            data_after
        )

    def test_process_task_worker(self):
        data_before = self.monit_task.get_data()
        data_before['task']['worker'] = factories.Worker().get_data()

        parkkeeper.datatools.task.process_task_data(data_before)

        task = models.MonitTask.objects.get(pk=self.monit_task.pk)
        data_after = task.get_data()

        self.assertEqual(
            data_before,
            data_after
        )

    @mock.patch('parkkeeper.datatools.task.cancel_double')
    def test_process_task_result(self, cancel_double_mock):
        data_before = self.monit_task.get_data()
        data_before['task']['result'] = factories.Result().get_data()

        parkkeeper.datatools.task.process_task_data(data_before)

        task = models.MonitTask.objects.get(pk=self.monit_task.pk)
        data_after = task.get_data()

        self.assertEqual(
            data_before,
            data_after
        )
        self.assertTrue(cancel_double_mock.called)

    def test_cancel_dead_worker_tasks(self):
        worker_absent = factories.Worker()
        worker_present = factories.Worker()
        factories.CurrentWorker(main=worker_present)
        workers = (worker_absent, worker_present)
        for worker in workers:
            factories.MonitTask(worker=worker, start_dt=now())
            factories.WorkTask(worker=worker, start_dt=now())

        # exists all
        for worker in workers:
            self.assertTrue(models.MonitTask.objects.filter(worker=worker, cancel_dt=None))
            self.assertTrue(models.WorkTask.objects.filter(worker=worker, cancel_dt=None))

        parkkeeper.datatools.task.cancel_dead_worker_tasks()

        # absent worker tasks canceled
        absent_worker_monit_tasks = models.MonitTask.objects.get(worker=worker_absent)
        absent_worker_work_tasks = models.WorkTask.objects.get(worker=worker_absent)
        for task in (absent_worker_monit_tasks, absent_worker_work_tasks):
            self.assertTrue(task.cancel_dt)
            self.assertEqual(task.cancel_reason, WORKER_DEAD_CANCEL_REASON)

        # present worker tasks not canceled
        present_worker_monit_tasks = models.MonitTask.objects.get(worker=worker_present)
        present_worker_work_tasks = models.WorkTask.objects.get(worker=worker_present)
        for task in (present_worker_monit_tasks, present_worker_work_tasks):
            self.assertIsNone(task.cancel_dt)
            self.assertFalse(task.cancel_reason)