# coding: utf-8
import multiprocessing
import asyncio
from typing import Callable

from django.conf import settings
import zmq
from parkkeeper.base import StoppableMixin


def emit_event(topic_filter: bytes, msg: str = ''):
    msg = msg.encode('utf-8')

    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect("tcp://%s:%s" % (settings.ZMQ_SERVER_ADDRESS, settings.ZMQ_EVENT_RECEIVER_PORT))
    socket.send_multipart([topic_filter, msg])
    socket.close()


def get_sub_socket(topic_filter: bytes, context: zmq.Context = None) -> zmq.Socket:
    if not context:
        context = zmq.Context()
    subscriber_socket = context.socket(zmq.SUB)
    subscriber_socket.connect("tcp://%s:%s" % (settings.ZMQ_SERVER_ADDRESS, settings.ZMQ_EVENT_PUBLISHER_PORT))
    subscriber_socket.setsockopt(zmq.SUBSCRIBE, topic_filter)
    return subscriber_socket


async def async_recv_event(subscriber_socket: zmq.Socket,
                           is_stopped: Callable[[], bool]=None,
                           sleep_period: float=0.1) -> str:
    if is_stopped is None:
        def is_stopped():
            return False

    while not is_stopped():
        try:
            [_, msg] = subscriber_socket.recv_multipart(flags=zmq.NOBLOCK)
            return msg.decode('utf-8')
        except zmq.error.Again:
            pass
        await asyncio.sleep(sleep_period)


class EventProcessor(StoppableMixin):

    def __init__(self, verbose: bool=False, sleep_period: float=0.1):
        super().__init__()
        self.context = zmq.Context()
        self.verbose = verbose
        self.sleep_period = sleep_period

    async def process(self):
        context = zmq.Context()

        receiver_socket = context.socket(zmq.PULL)
        receiver_socket.bind("tcp://*:%s" % settings.ZMQ_EVENT_RECEIVER_PORT)

        publisher_socket = context.socket(zmq.PUB)
        publisher_socket.bind("tcp://*:%s" % settings.ZMQ_EVENT_PUBLISHER_PORT)

        if self.verbose:
            print('EventPublisher started.')

        while not self.is_stopped():
            try:
                [topic_filter, msg] = receiver_socket.recv_multipart(flags=zmq.NOBLOCK)
                publisher_socket.send_multipart([topic_filter, msg])
            except zmq.Again:
                await asyncio.sleep(self.sleep_period)

        receiver_socket.close()
        publisher_socket.close()
        context.term()
