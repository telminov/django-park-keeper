# coding: utf-8
import asyncio
import json
import datetime
import zmq
from unittest import mock

from bson import json_util
from django.test import TestCase
from django.utils.timezone import now
from djutils.testrunner import TearDownTestCaseMixin
from parkkeeper.worker_processor import WorkerProcessor
from parkkeeper import factories
from parkkeeper import models
from parkworker.const import WORKER_HEART_BEAT_PERIOD


class WorkerProcessorCase(TearDownTestCaseMixin, TestCase):

    def setUp(self):
        self.processor = WorkerProcessor(sleep_period=0.01)
        self.processor.context = mock.Mock()

    def tearDown(self):
        self.tearDownMongo()

    async def stop_processor(self):
        await asyncio.sleep(0.005)
        self.processor.stop()

    @mock.patch('parkkeeper.worker_processor.process_worker_data')
    def test_process_workers(self, process_worker_mock):
        subscriber_socket_mock = self.processor.context.socket.return_value

        data = {'msg': 'test message'}
        data_json = json.dumps(data).encode('utf-8')
        multipart_msg = [b'test_filter', data_json]
        subscriber_socket_mock.recv_multipart.side_effect = (multipart_msg, zmq.Again())

        loop = asyncio.get_event_loop()
        loop.create_task(self.stop_processor())
        loop.run_until_complete(self.processor.process_workers())

        self.assertEqual(1, process_worker_mock.call_count)
        self.assertEqual(
            process_worker_mock.call_args,
            mock.call(data)
        )

    @mock.patch('parkkeeper.worker_processor.process_worker_data')
    def test_register_workers(self, process_worker_mock):
        registrator_socket_mock = self.processor.context.socket.return_value

        worker_data = {
            'main': factories.Worker().to_mongo().to_dict(),
            'monits': {'test_monit1': 'description1', 'test_monit2': 'description2'},
            'works': {'test_work1': 'description1', 'test_work2': 'description2'},
        }

        self.assertFalse(models.WorkerType.objects.exists())
        self.assertFalse(models.Monit.objects.exists())
        self.assertFalse(models.Work.objects.exists())

        worker_data_json = json.dumps(worker_data, default=json_util.default).encode('utf-8')
        registrator_socket_mock.recv_string.side_effect = (worker_data_json, zmq.Again())

        loop = asyncio.get_event_loop()
        loop.create_task(self.stop_processor())
        loop.run_until_complete(self.processor.register_workers())

        self.assertEqual(1, process_worker_mock.call_count)
        self.assertEqual(
            process_worker_mock.call_args,
            mock.call(worker_data)
        )

        self.assertTrue(models.WorkerType.objects.filter(name=worker_data['main']['type']).exists())
        for monit_name in worker_data['monits'].keys():
            self.assertTrue(models.Monit.objects.filter(name=monit_name).exists())
        for work_name in worker_data['works'].keys():
            self.assertTrue(models.Work.objects.filter(name=work_name).exists())

    def test_clear_dead_workers_not_delete_actual(self):
        heart_beat_dt = now()
        actual_worker = factories.CurrentWorker(heart_beat_dt=heart_beat_dt)

        loop = asyncio.get_event_loop()
        loop.create_task(self.stop_processor())
        loop.run_until_complete(self.processor.clear_dead_workers())

        self.assertTrue(models.CurrentWorker.objects.filter(pk=actual_worker.pk).count())

    def test_clear_dead_workers_delete_not_actual(self):
        heart_beat_dt = now() - datetime.timedelta(seconds=WORKER_HEART_BEAT_PERIOD * 2)
        not_actual_worker = factories.CurrentWorker(heart_beat_dt=heart_beat_dt)

        self.assertTrue(models.CurrentWorker.objects.filter(pk=not_actual_worker.pk).count())

        loop = asyncio.get_event_loop()
        loop.create_task(self.stop_processor())
        loop.run_until_complete(self.processor.clear_dead_workers())

        self.assertFalse(models.CurrentWorker.objects.filter(pk=not_actual_worker.pk).count())