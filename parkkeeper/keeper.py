# coding: utf-8
import socket
import multiprocessing
from time import sleep
import uuid
from django.conf import settings
from django.utils.timezone import now
from parkkeeper.event_publisher import EventPublisher, MONIT_STATUS_EVENT, MONIT_WORKER_EVENT, MONIT_TASK_EVENT
import zmq

from parkkeeper import models
from parkkeeper.monits.base import Monit


class MonitScheduler(multiprocessing.Process):

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.bind("tcp://*:%s" % (settings.ZMQ_MONIT_SCHEDULER_PORT, ))
        print('MonitScheduler started.')

        # cancel not started tasks
        models.MonitTask.objects.filter(start_dt=None).update(cancel_dt=now())

        while True:
            tasks = models.MonitSchedule.create_tasks()
            if tasks:
                # task created event
                EventPublisher.emit_event(MONIT_TASK_EVENT)
                # send monit tasks for workers
                for task in tasks:
                    socket.send_json(task.to_json())
            sleep(1)


class MonitWorker(multiprocessing.Process):
    uuid = None
    worker_id = None
    created_dt = None
    host_name = None

    def setup(self, worker_id=None):
        self.uuid = str(uuid.uuid4())
        self.created_dt = now()
        self.host_name = socket.gethostname()

        if worker_id is None:
            worker_id = self.uuid
        self.worker_id = str(worker_id)

    def run(self):
        context = zmq.Context()

        task_socket = context.socket(zmq.PULL)
        task_socket.connect("tcp://%s:%s" % (settings.ZMQ_SERVER_ADDRESS, settings.ZMQ_MONIT_SCHEDULER_PORT))

        print('Worker start %s' % self.worker_id)

        while True:
            task_json = task_socket.recv_json()
            task = models.MonitTask.from_json(task_json)
            print("Worker %s. Received request: %s for %s" % (self.worker_id, task.monit_name, task.host_address))

            monit_name = task.monit_name
            monit_class = Monit.get_monit(monit_name)
            monit = monit_class()

            task.start_dt = now()
            task.worker = self.get_worker()
            task.save()
            # worker busy
            EventPublisher.emit_event(MONIT_WORKER_EVENT, task.worker.to_json())

            result = monit.check(
                host=task.host_address,
                options=task.options,
            )
            task.result = result
            task.save()
            task_json = task.to_json()

            print('Worker %s result is_success: %s' % (self.worker_id, task.result.is_success))
            # get new monitoring results
            EventPublisher.emit_event(MONIT_STATUS_EVENT, task_json)
            # worker free event
            EventPublisher.emit_event(MONIT_WORKER_EVENT, task.worker.to_json())
            # task completed event
            EventPublisher.emit_event(MONIT_TASK_EVENT)

    def get_worker(self) -> models.Worker:
        return models.Worker(
            id=self.worker_id,
            uuid=self.uuid,
            created_dt=self.created_dt,
            host_name=self.host_name,
        )
