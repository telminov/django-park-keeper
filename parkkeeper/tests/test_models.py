# coding: utf-8

from django.test import TestCase
from djutils.testrunner import TearDownTestCaseMixin
from parkkeeper import models
from parkkeeper import factories


class BaseTaskTestCase(TearDownTestCaseMixin, TestCase):

    def tearDown(self):
        self.tearDownMongo()

    def test_get_task_model_monit(self):
        monit_task = factories.MonitTask()
        task_type = monit_task.get_task_type()
        task_model = models.BaseTask.get_task_model(task_type)
        self.assertEqual(
            task_model,
            models.MonitTask
        )

    def test_get_task_model_work(self):
        work_task = factories.WorkTask()
        task_type = work_task.get_task_type()
        task_model = models.BaseTask.get_task_model(task_type)
        self.assertEqual(
            task_model,
            models.WorkTask
        )
