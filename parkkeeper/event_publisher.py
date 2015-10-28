# coding: utf-8
import multiprocessing
import asyncio
from django.conf import settings
from django.utils.timezone import now
import zmq


class EventPublisher(multiprocessing.Process):

    @staticmethod
    def emit_event(msg):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.connect("tcp://%s:%s" % (settings.ZMQ_SERVER_ADDRESS, settings.ZMQ_EVENT_RECEIVER_PORT))
        socket.send_string(msg)
        socket.close()

    @staticmethod
    async def recv_event():
        context = zmq.Context()
        subscriber_socket = context.socket(zmq.SUB)
        subscriber_socket.connect("tcp://%s:%s" % (settings.ZMQ_SERVER_ADDRESS, settings.ZMQ_EVENT_PUBLISHER_PORT))
        subscriber_socket.setsockopt(zmq.SUBSCRIBE, b'')

        try:
            while True:
                print('EventPublisher recv_event heart beat', now().isoformat())
                try:
                    msg = subscriber_socket.recv_string(flags=zmq.NOBLOCK)
                    return msg
                except zmq.error.Again:
                    pass
                await asyncio.sleep(0.5)
        finally:
            subscriber_socket.close()


    def run(self):
        context = zmq.Context()

        receiver_socket = context.socket(zmq.PULL)
        receiver_socket.bind("tcp://*:%s" % settings.ZMQ_EVENT_RECEIVER_PORT)

        publisher_socket = context.socket(zmq.PUB)
        publisher_socket.bind("tcp://*:%s" % settings.ZMQ_EVENT_PUBLISHER_PORT)

        print('EventPublisher started.')

        while True:
            msg = receiver_socket.recv_string()
            print('EventPublisher msg', msg)
            publisher_socket.send_string(msg)

        receiver_socket.close()
        publisher_socket.close()
        context.term()
