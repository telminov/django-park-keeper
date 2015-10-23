# coding: utf-8
import multiprocessing
from time import sleep
import uuid
import random
import zmq


class MonitScheduler(multiprocessing.Process):

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.bind("tcp://*:5559")
        print('MonitScheduler started.')

        while True:
            for _ in [1, 2]:
                msg = str(random.randint(1, 100))
                socket.send_string(msg)
                print('Send message %s' % msg)
            sleep(5)


class MonitResultCollector(multiprocessing.Process):

    def run(self):
        context = zmq.Context()

        result_socket = context.socket(zmq.PULL)
        result_socket.bind("tcp://*:5560")
        print('MonitResultCollector started.')

        # Switch messages between sockets
        while True:
            result = result_socket.recv_string()
            print(result)


class MonitWorker(multiprocessing.Process):
    worker_id = None

    def setup(self, worker_id=None):
        if worker_id is None:
            worker_id = str(uuid.uuid4())
        self.worker_id = worker_id

    def run(self):
        context = zmq.Context()

        task_socket = context.socket(zmq.PULL)
        task_socket.connect("tcp://localhost:5559")

        result_socket = context.socket(zmq.PUSH)
        result_socket.connect("tcp://localhost:5560")

        print('Worker start %s' % self.worker_id)

        while True:
            task = task_socket.recv_string()
            sleep(1)
            print("Worker %s. Received request: %s" % (self.worker_id, task))
            result = 'Worker %s process %s' % (self.worker_id, task)
            result_socket.send_string(result)
