# coding: utf-8
import asyncio
import zmq
from unittest import mock

from django.test import TestCase
from parkkeeper import event


class EventTestCase(TestCase):
    def setUp(self):
        self._is_stopped = False

    def is_stopped(self) -> bool:
        return self._is_stopped

    async def stop_delay(self):
        await asyncio.sleep(0.05)
        self._is_stopped = True

    @mock.patch('parkkeeper.event.zmq.Context', spec_set=zmq.Context)
    def test_event_emit(self, context_mock):
        topic_filter = b'test_filter'
        msg = 'test msg'
        event.emit_event(topic_filter, msg)

        socket_mock = context_mock.return_value.socket.return_value
        self.assertTrue(socket_mock.send_multipart.called)

        call_filter = socket_mock.send_multipart.call_args[0][0][0]
        self.assertEqual(topic_filter, call_filter)

        call_msg = socket_mock.send_multipart.call_args[0][0][1]
        self.assertEqual(msg.encode('utf-8'), call_msg)

    @mock.patch('parkkeeper.event.zmq.Context', spec_set=zmq.Context)
    def test_get_sub_socket(self, context_mock):
        topic_filter = b'test_filter'
        event.get_sub_socket(topic_filter)

        socket_mock = context_mock.return_value.socket.return_value
        self.assertTrue(socket_mock.connect.called)
        self.assertTrue(socket_mock.setsockopt.called)

    @mock.patch('parkkeeper.event.zmq.Socket', spec_set=zmq.Socket)
    def test_async_recv_event(self, socket_mock):
        topic_filter = b'test_filter'
        msg = b'test msg'
        socket_mock.recv_multipart.return_value = [topic_filter, msg]

        coro_recv_event = event.async_recv_event(socket_mock, self.is_stopped)

        loop = asyncio.get_event_loop()
        loop.create_task(self.stop_delay())
        recv_msg = loop.run_until_complete(coro_recv_event)

        self.assertEqual(
            msg.decode('utf-8'),
            recv_msg
        )


class EventProcessorTestCase(TestCase):

    def setUp(self):
        self.processor = event.EventProcessor(sleep_period=0.01)
        self.processor.context = mock.Mock()

    async def stop_processor(self):
        await asyncio.sleep(0.005)
        self.processor.stop()

    @mock.patch('parkkeeper.event.zmq.Context', spec_set=zmq.Context)
    def test_process(self, context_mock):
        receiver_socket = mock.Mock()
        publisher_socket = mock.Mock()
        context_mock.return_value.socket.side_effect = (receiver_socket, publisher_socket)

        multipart_msg = [b'test_filter', b'test msg']
        receiver_socket.recv_multipart.side_effect = (multipart_msg, zmq.Again())

        loop = asyncio.get_event_loop()
        loop.create_task(self.stop_processor())
        loop.run_until_complete(self.processor.process())

        self.assertEqual(1, publisher_socket.send_multipart.call_count)
        self.assertEqual(
            publisher_socket.send_multipart.call_args,
            mock.call(multipart_msg)
        )
