# coding: utf-8
import multiprocessing
from time import sleep
import uuid
import random
import zmq

STOP_MSG = 'STOP'


class Requester:
    def start(self):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.bind("tcp://*:5559")
        print('Requester start')

        while True:
            for _ in [1, 2]:
                msg = str(random.randint(1, 100))
                socket.send_string(msg)
                print('Send message %s' % msg)
            sleep(5)

class Worker(multiprocessing.Process):
    worker_id = None

    def setup(self, worker_id):
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

class Sink:
    def start(self):
        context = zmq.Context()

        result_socket = context.socket(zmq.PULL)
        result_socket.bind("tcp://*:5560")

        # Switch messages between sockets
        while True:
            result = result_socket.recv_string()
            print(result)

#
# class Keeper:
#
#     def __init__(self, monits_count=2):
#         self.monit_workers_count = monits_count
#         self.monit_workers = []
#
#     def start_loop(self):
#         self._start_monits()
#
#         try:
#             while True:
#                 for w in self._get_alive_monit_workers():
#                     task = str(random.randint(1, 100))
#                     self.add_monit_task(task)
#
#                 sleep(1)
#         finally:
#             print('Stop them all!..')
#             self._stop_workers()
#             sleep(1)
#
#     def add_monit_task(self, task):
#         pass
#
#     def _stop_workers(self):
#         for w in self._get_alive_monit_workers():
#             self.add_monit_task(STOP_MSG)
#
#     def _get_alive_monit_workers(self):
#         return [w for w in self.monit_workers if w.is_alive()]
#
#
# class MonitWorker:
#     worker_id = None
#
#     def __init__(self, worker_id: str=None):
#         self.worker_id = worker_id or str(uuid.uuid4())
#         self.context = zmq.Context()
#         receiver = self.context.socket(zmq.)
#
#     def run(self):
#         print('working %s started' % self.worker_id)
#
#         while True:
#             task = self.task_queue.get()
#             sleep(0.5)
#
#             if task == Keeper.STOP_MSG:
#                 print('working %s stopped' % self.worker_id)
#                 break
#
#             print('monit %s working: %s...' % (self.worker_id, task))
