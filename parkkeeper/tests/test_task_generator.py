# coding: utf-8
import asyncio
import json
import zmq
from unittest import mock

from django.test import TestCase
from djutils.testrunner import TearDownTestCaseMixin
from parkkeeper.task_generator import TaskGenerator, TaskQueue
from parkkeeper import models
from parkkeeper import factories
from parkworker.const import TASK_TYPE_MONIT, TASK_TYPE_WORK, FRESH_TASK_CANCEL_REASON, \
    TASK_GENERATOR_RESTART_CANCEL_REASON, TASK_EVENT


class TaskGeneratorTestCase(TearDownTestCaseMixin, TestCase):

    def setUp(self):
        self.generator = TaskGenerator(sleep_period=0.01)
        self.generator.context = mock.Mock(spec_set=zmq.Context)

    def tearDown(self):
        self.tearDownMongo()

    async def stop_generator(self):
        await asyncio.sleep(0.005)
        self.generator.stop()

    @mock.patch('parkkeeper.task_generator.TaskGenerator.cancel_not_started_tasks')
    def test_init_cancel_not_started_tasks(self, cancel_mock):
        TaskGenerator()
        self.assertTrue(cancel_mock.called)

    def test_cancel_not_started_tasks(self):
        monit_task = factories.MonitTask()
        work_task = factories.WorkTask()

        TaskGenerator.cancel_not_started_tasks()

        monit_task = models.MonitTask.objects.get(pk=monit_task.pk)
        self.assertTrue(monit_task.cancel_dt)
        self.assertEqual(monit_task.cancel_reason, TASK_GENERATOR_RESTART_CANCEL_REASON)

        work_task = models.WorkTask.objects.get(pk=work_task.pk)
        self.assertTrue(work_task.cancel_dt)
        self.assertEqual(work_task.cancel_reason, TASK_GENERATOR_RESTART_CANCEL_REASON)

    @mock.patch('parkkeeper.task_generator.emit_event')
    @mock.patch('parkkeeper.task_generator.models.MonitSchedule.create_tasks')
    def test_generate_monit_tasks(self, create_tasks_mock, emit_mock):
        monit = factories.Monit()
        monit_tasks = factories.MonitTask.create_batch(monit_name=monit.name, size=2)
        create_tasks_mock.return_value = monit_tasks

        loop = asyncio.get_event_loop()
        loop.create_task(self.stop_generator())
        loop.run_until_complete(self.generator.generate_monit_tasks())

        self.assertEqual(
            emit_mock.call_count,
            len(monit_tasks),
        )

        for task in monit_tasks:
            self.assertIn(
                mock.call(TASK_EVENT, task.get_json()),
                emit_mock.call_args_list
            )

    @mock.patch('parkkeeper.task_generator.emit_event')
    @mock.patch('parkkeeper.task_generator.models.WorkSchedule.create_tasks')
    def test_generate_work_tasks(self, create_tasks_mock, emit_mock):
        work = factories.Work()
        work_tasks = factories.WorkTask.create_batch(work_name=work.name, size=2)
        create_tasks_mock.return_value = work_tasks

        loop = asyncio.get_event_loop()
        loop.create_task(self.stop_generator())
        loop.run_until_complete(self.generator.generate_work_tasks())

        self.assertEqual(
            emit_mock.call_count,
            len(work_tasks),
        )

        for task in work_tasks:
            self.assertIn(
                mock.call(TASK_EVENT, task.get_json()),
                emit_mock.call_args_list
            )

    @mock.patch.object(TaskGenerator, '_push_for_workers')
    def test_push_tasks(self, push_mock):
        monit = factories.Monit()
        tasks = factories.MonitTask.create_batch(monit_name=monit.name, size=2)
        for task in tasks:
            self.generator.tasks.add_task(task)

        loop = asyncio.get_event_loop()
        loop.create_task(self.stop_generator())
        loop.run_until_complete(self.generator.push_tasks())

        call_worker_type = push_mock.call_args[0][0]
        self.assertEqual(call_worker_type, monit.worker_type.name)

        call_tasks = push_mock.call_args[0][1]
        self.assertEqual(len(call_tasks), len(tasks))
        for task in call_tasks:
            self.assertIn(task, tasks)

    @mock.patch.object(TaskGenerator, '_get_socket')
    def test_push_for_workers(self, get_socket_mock):
        monit = factories.Monit()
        work = factories.Work()

        tasks = []
        tasks.extend(factories.MonitTask.create_batch(monit_name=monit.name, size=2))
        tasks.extend(factories.WorkTask.create_batch(work_name=work.name, size=2))

        self.generator._push_for_workers(monit.worker_type, tasks)
        self.assertTrue(get_socket_mock.called)

        socket_mock = get_socket_mock.return_value
        self.assertTrue(socket_mock.send_string.called)
        self.assertEqual(
            len(socket_mock.send_string.call_args_list),
            len(tasks)
        )
        for call_args in socket_mock.send_string.call_args_list:
            call_task_json = call_args[0][0]
            self.assertIn(
                call_task_json,
                [task.get_json() for task in tasks]
            )

    def test_create_pool(self):
        factories.WorkerType.create_batch(size=3)
        self.generator._create_pool()
        self.assertEquals(
            models.WorkerType.objects.all().count(),
            len(self.generator._socket_pool)
        )

    def test_close_pool(self):
        factories.WorkerType.create_batch(size=3)
        self.generator._create_pool()
        self.generator._close_pool()
        self.assertTrue(
            all([s.close.called for s in self.generator._socket_pool.values()])
        )

    def test_get_socket(self):
        self.generator._create_pool()
        self.assertFalse(self.generator._socket_pool)

        worker_type = factories.WorkerType()
        socket1 = self.generator._get_socket(worker_type)
        self.assertEqual(1, len(self.generator._socket_pool))

        socket2 = self.generator._get_socket(worker_type)
        self.assertEqual(1, len(self.generator._socket_pool))
        self.assertIs(socket1, socket2)

    def test_create_socket(self):
        self.generator._create_pool()
        worker_type = factories.WorkerType()
        socket = self.generator._create_socket(worker_type)
        self.assertIn(socket, self.generator._socket_pool.values())

    def test_get_monit_task_json(self):
        monit = factories.Monit()
        task = factories.MonitTask(monit_name=monit.name)

        loaded_task = json.loads(task.get_json())

        self.assertEqual(TASK_TYPE_MONIT, loaded_task['type'])
        self.assertEqual(str(task.pk), loaded_task['task']['id'])
        self.assertEqual(task.monit_name, loaded_task['task']['monit_name'])


class TaskQueueTestCase(TearDownTestCaseMixin, TestCase):
    def setUp(self):
        self.queue = TaskQueue()

    def tearDown(self):
        self.tearDownMongo()

    def test_add_monit_task(self):
        monit = factories.Monit()
        monit_task = factories.MonitTask(monit_name=monit.name)

        self.assertFalse(self.queue.tasks)
        self.queue.add_task(monit_task)
        self.assertTrue(self.queue.tasks)

        key = self.queue._get_key(monit_task)
        self.assertEqual(
            self.queue.tasks[monit.worker_type.name][key],
            monit_task
        )

    @mock.patch('parkkeeper.task_generator.TaskQueue._cancel_task')
    def test_add_monit_task_cancel_old(self, cancel_mock):
        monit = factories.Monit()

        monit_task1 = factories.MonitTask(monit_name=monit.name)
        self.queue.add_task(monit_task1)
        self.assertFalse(cancel_mock.called)

        monit_task2 = factories.MonitTask(monit_name=monit.name, host_address=monit_task1.host_address)
        self.queue.add_task(monit_task2)
        self.assertTrue(cancel_mock.called)

    def test_add_work_task(self):
        work = factories.Work()
        work_task = factories.WorkTask(work_name=work.name)

        self.assertFalse(self.queue.tasks)
        self.queue.add_task(work_task)
        self.assertTrue(self.queue.tasks)

        key = self.queue._get_key(work_task)
        self.assertEqual(
            self.queue.tasks[work.worker_type.name][key],
            work_task
        )

    @mock.patch('parkkeeper.task_generator.TaskQueue._cancel_task')
    def test_add_work_task_cancel_old(self, cancel_mock):
        work = factories.Work()

        work_task1 = factories.WorkTask(work_name=work.name)
        self.queue.add_task(work_task1)
        self.assertFalse(cancel_mock.called)

        work_task2 = factories.WorkTask(work_name=work.name, host_address=work_task1.host_address)
        self.queue.add_task(work_task2)
        self.assertTrue(cancel_mock.called)

    def test_get_tasks_by_worker_type(self):
        tasks_by_worker_type = {}
        for w_t in factories.WorkerType.create_batch(size=2):
            tasks_by_worker_type[w_t.name] = []

            monit = factories.Monit(worker_type=w_t)
            monit_task = factories.MonitTask(monit_name=monit.name)
            self.queue.add_task(monit_task)
            tasks_by_worker_type[w_t.name].append(monit_task)

            work = factories.Work(worker_type=w_t)
            work_task = factories.WorkTask(work_name=work.name)
            self.queue.add_task(work_task)
            tasks_by_worker_type[w_t.name].append(work_task)

        queue_tasks_by_worker_type = self.queue.get_tasks_by_worker_type()
        self.assertEqual(
            queue_tasks_by_worker_type.keys(),
            tasks_by_worker_type.keys(),
        )

        for w_t_name in tasks_by_worker_type.keys():
            self.assertEqual(
                len(tasks_by_worker_type[w_t_name]),
                len(queue_tasks_by_worker_type[w_t_name]),
            )
            for task in tasks_by_worker_type[w_t_name]:
                self.assertIn(
                    task,
                    queue_tasks_by_worker_type[w_t_name]
                )

    def test_get_monit_key(self):
        task = factories.MonitTask()
        key = TaskQueue._get_key(task)
        self.assertEqual(
            (TASK_TYPE_MONIT, task.host_address, task.monit_name),
            key
        )

    def test_get_work_key(self):
        task = factories.WorkTask()
        key = TaskQueue._get_key(task)
        self.assertEqual(
            (TASK_TYPE_WORK, task.host_address, task.work_name),
            key
        )

    @mock.patch('parkkeeper.task_generator.emit_event')
    def test_cancel_monit_task(self, emit_event_mock):
        task = factories.MonitTask()
        self.assertFalse(task.cancel_dt)
        self.assertFalse(task.cancel_reason)

        self.queue._cancel_task(task)

        task = models.MonitTask.objects.get(pk=task.pk)
        self.assertTrue(task.cancel_dt)
        self.assertEqual(task.cancel_reason, FRESH_TASK_CANCEL_REASON)
        self.assertTrue(emit_event_mock.called)

    @mock.patch('parkkeeper.task_generator.emit_event')
    def test_cancel_work_task(self, emit_event_mock):
        task = factories.WorkTask()
        self.assertFalse(task.cancel_dt)
        self.assertFalse(task.cancel_reason)

        self.queue._cancel_task(task)

        task = models.WorkTask.objects.get(pk=task.pk)
        self.assertTrue(task.cancel_dt)
        self.assertEqual(task.cancel_reason, FRESH_TASK_CANCEL_REASON)
        self.assertTrue(emit_event_mock.called)
