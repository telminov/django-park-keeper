# coding: utf-8
import multiprocessing
import asyncio
from django.conf import settings
from django.utils.timezone import now
import zmq

MONIT_STATUS_EVENT = b'MONIT_STATUS_EVENT'
MONIT_TASK_EVENT = b'MONIT_TASK_EVENT'
MONIT_WORKER_EVENT = b'MONIT_WORKER_EVENT'

class EventPublisher(multiprocessing.Process):

    @staticmethod
    def emit_event(topic_filter, msg=''):
        msg = msg.encode('utf-8')

        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.connect("tcp://%s:%s" % (settings.ZMQ_SERVER_ADDRESS, settings.ZMQ_EVENT_RECEIVER_PORT))
        socket.send_multipart([topic_filter, msg])
        socket.close()

    @staticmethod
    async def recv_event(topic_filter):
        context = zmq.Context()
        subscriber_socket = context.socket(zmq.SUB)
        subscriber_socket.connect("tcp://%s:%s" % (settings.ZMQ_SERVER_ADDRESS, settings.ZMQ_EVENT_PUBLISHER_PORT))
        subscriber_socket.setsockopt(zmq.SUBSCRIBE, topic_filter)

        try:
            while True:
                print('EventPublisher recv_event heart beat', now().isoformat())
                try:
                    [topic_filter, msg] = subscriber_socket.recv_multipart(flags=zmq.NOBLOCK)
                    print('EventPublisher recv_event got ', topic_filter, msg)
                    return msg.decode('utf-8')
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
            [topic_filter, msg] = receiver_socket.recv_multipart()
            print('EventPublisher msg', topic_filter, msg)
            publisher_socket.send_multipart([topic_filter, msg])

        receiver_socket.close()
        publisher_socket.close()
        context.term()
