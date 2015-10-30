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

        self.cancel_not_started_tasks()
        # TODO: add to hear beats processing
        self.cancel_dead_worker_tasks()

        while True:
            tasks = models.MonitSchedule.create_tasks()
            if tasks:
                # task created event
                EventPublisher.emit_event(MONIT_TASK_EVENT)
                # send monit tasks for workers
                for task in tasks:
                    socket.send_json(task.to_json())
            sleep(1)

    @staticmethod
    def cancel_not_started_tasks():
        models.MonitTask.objects\
            .filter(start_dt=None)\
            .update(cancel_dt=now(), cancel_reason='restart monit scheduler')

    @staticmethod
    def cancel_dead_worker_tasks():
        current_worker_uuids = models.CurrentWorker.objects.values_list('info__uuid')
        models.MonitTask.objects\
            .filter(start_dt__ne=None, result__dt=None, cancel_dt=None,
                    worker__uuid__not__in=current_worker_uuids)\
            .update(cancel_dt=now(), cancel_reason='monit worker not alive')

# TODO: add worker status publishing (heart beat)
class MonitWorker(multiprocessing.Process):
    current_worker = None

    def setup(self, worker_id=None):
        if worker_id is None:
            worker_id = self.uuid

        self.current_worker = models.CurrentWorker.objects.create(
            info=models.Worker(
                uuid=str(uuid.uuid4()),
                id=str(worker_id),
                created_dt=now(),
                host_name=socket.gethostname()
            )
        )

    def run(self):
        context = zmq.Context()

        task_socket = context.socket(zmq.PULL)
        task_socket.connect("tcp://%s:%s" % (settings.ZMQ_SERVER_ADDRESS, settings.ZMQ_MONIT_SCHEDULER_PORT))

        print('Worker start %s' % self.get_worker().id)

        try:
            while True:
                task_json = task_socket.recv_json()
                task = models.MonitTask.from_json(task_json)
                print("Worker %s. Received request: %s for %s" % (self.get_worker().id, task.monit_name, task.host_address))

                monit_name = task.monit_name
                monit_class = Monit.get_monit(monit_name)
                monit = monit_class()

                self.register_start_task(task)

                result = monit.check(
                    host=task.host_address,
                    options=task.options,
                )

                self.register_complete_task(task, result)

                # get new monitoring results
                EventPublisher.emit_event(MONIT_STATUS_EVENT, task.to_json())
        finally:
            models.CurrentWorker.objects.filter(id=self.current_worker.id).delete()

    def get_worker(self) -> models.Worker:
        return self.current_worker.info

    def add_current_task(self, task):
        # self.current_worker.update(add_to_set__tasks=task.id)
        self.current_worker.task_ids.append(task.id)
        self.current_worker.save()
        EventPublisher.emit_event(MONIT_WORKER_EVENT, self.current_worker.to_json())
        # print('add_current_task', self.current_worker.to_json())

    def rm_current_task(self, task):
        # self.current_worker.update(pull__tasks=task.id)
        self.current_worker.task_ids = [t_id for t_id in self.current_worker.task_ids if t_id != task.id]
        self.current_worker.save()
        EventPublisher.emit_event(MONIT_WORKER_EVENT, self.current_worker.to_json())
        # print('rm_current_task', self.current_worker.to_json())

    def register_start_task(self, task):
        task.start_dt = now()
        task.worker = self.get_worker()
        task.save()
        # task create event
        EventPublisher.emit_event(MONIT_TASK_EVENT)

        self.add_current_task(task)

    def register_complete_task(self, task, result):
            task.result = result
            task.save()
            # task completed event
            EventPublisher.emit_event(MONIT_TASK_EVENT)

            self.rm_current_task(task)

            print('Worker %s result is_success: %s' % (self.get_worker().id, task.result.is_success))
