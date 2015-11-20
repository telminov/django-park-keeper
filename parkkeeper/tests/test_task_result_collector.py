# coding: utf-8
import asyncio
import json
import zmq
from unittest import mock

from django.test import TestCase
from djutils.testrunner import TearDownTestCaseMixin
from parkkeeper.task_result_collector import TaskResultCollector


class EventTestCase(TearDownTestCaseMixin, TestCase):
    def setUp(self):
        self.collector = TaskResultCollector(sleep_period=0.01)
        self.collector.context = mock.Mock(spec_set=zmq.Context)

    def tearDown(self):
        self.tearDownMongo()

    async def stop_collector(self):
        await asyncio.sleep(0.005)
        self.collector.stop()

    @mock.patch('parkkeeper.task_result_collector.process_task_data')
    def test_collect_tasks(self, process_task_mock):
        subscriber_socket_mock = self.collector.context.socket.return_value

        data = {'msg': 'test message'}
        data_json = json.dumps(data).encode('utf-8')
        multipart_msg = [b'test_filter', data_json]
        subscriber_socket_mock.recv_multipart.side_effect = (multipart_msg, zmq.Again())

        loop = asyncio.get_event_loop()
        loop.create_task(self.stop_collector())
        loop.run_until_complete(self.collector.collect_tasks())

        self.assertEqual(1, process_task_mock.call_count)
        self.assertEqual(
            process_task_mock.call_args,
            mock.call(data)
        )
