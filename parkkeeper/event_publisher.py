# coding: utf-8
import multiprocessing
from django.conf import settings
import zmq


class EventPublisher(multiprocessing.Process):

    @staticmethod
    def emit_event(msg):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.connect("tcp://%s:%s" % (settings.ZMQ_SERVER_ADDRESS, settings.ZMQ_EVENT_RECEIVER_PORT))
        socket.send_string(msg)
        socket.close()

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
