# coding: utf-8
import multiprocessing
from time import sleep
import uuid
import random
import zmq

from parkkeeper import models
from parkkeeper.monits.base import Monit

class MonitScheduler(multiprocessing.Process):

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.bind("tcp://*:5559")
        print('MonitScheduler started.')

        # TODO: load not done tasks

        while True:
            for task in models.MonitSchedule.create_tasks():
                print('Send %s for host %s' % (task.monit_name, task.host_address))
                socket.send_json(task.to_json())
            sleep(1)


class MonitResultCollector(multiprocessing.Process):

    def run(self):
        context = zmq.Context()

        result_socket = context.socket(zmq.PULL)
        result_socket.bind("tcp://*:5560")
        print('MonitResultCollector started.')

        # Switch messages between sockets
        while True:
            task_json = result_socket.recv_json()
            task = models.MonitTask.from_json(task_json)
            print('MonitResultCollector: task %s for host %s is_success %s' % (
                task.monit_name, task.host_address, task.result.is_success))


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
            task_json = task_socket.recv_json()
            task = models.MonitTask.from_json(task_json)
            print("Worker %s. Received request: %s for %s" % (self.worker_id, task.monit_name, task.host_address))

            monit_name = task.monit_name
            monit_class = Monit.get_monit(monit_name)
            monit = monit_class()
            result = monit.check(
                host=task.host_address,
                options=task.options,
            )
            task.result = result
            task.save()
            task_json = task.to_json()

            print('Worker %s result is_success: %s' % (self.worker_id, task.result.is_success))
            result_socket.send_json(task_json)
