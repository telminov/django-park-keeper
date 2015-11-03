# coding: utf-8
import multiprocessing
import asyncio
from django.conf import settings
import zmq


def emit_event(topic_filter: str, msg: str = ''):
    msg = msg.encode('utf-8')

    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect("tcp://%s:%s" % (settings.ZMQ_SERVER_ADDRESS, settings.ZMQ_EVENT_RECEIVER_PORT))
    socket.send_multipart([topic_filter, msg])
    socket.close()


def get_sub_socket(topic_filter: str, context: zmq.Context = None) -> zmq.Socket:
    if not context:
        context = zmq.Context()
    subscriber_socket = context.socket(zmq.SUB)
    subscriber_socket.connect("tcp://%s:%s" % (settings.ZMQ_SERVER_ADDRESS, settings.ZMQ_EVENT_PUBLISHER_PORT))
    subscriber_socket.setsockopt(zmq.SUBSCRIBE, topic_filter)
    return subscriber_socket


async def async_recv_event(subscriber_socket: zmq.Socket) -> str:
    while True:
        # print('EventPublisher recv_event heart beat', now().isoformat())
        try:
            [_, msg] = subscriber_socket.recv_multipart(flags=zmq.NOBLOCK)
            # print('EventPublisher recv_event got ', topic_filter, msg)
            return msg.decode('utf-8')
        except zmq.error.Again:
            pass
        await asyncio.sleep(0.1)


def recv_event(subscriber_socket: zmq.Socket) -> str:
    while True:
        # print('EventPublisher recv_event heart beat', now().isoformat())
        [_, msg] = subscriber_socket.recv_multipart()
        # print('EventPublisher recv_event got ', topic_filter, msg)
        return msg.decode('utf-8')


class EventProcessor(multiprocessing.Process):
    def run(self):
        context = zmq.Context()

        receiver_socket = context.socket(zmq.PULL)
        receiver_socket.bind("tcp://*:%s" % settings.ZMQ_EVENT_RECEIVER_PORT)

        publisher_socket = context.socket(zmq.PUB)
        publisher_socket.bind("tcp://*:%s" % settings.ZMQ_EVENT_PUBLISHER_PORT)

        print('EventPublisher started.')

        while True:
            [topic_filter, msg] = receiver_socket.recv_multipart()
            # print('EventPublisher recv msg for publish ', topic_filter, msg)
            publisher_socket.send_multipart([topic_filter, msg])

        receiver_socket.close()
        publisher_socket.close()
        context.term()
