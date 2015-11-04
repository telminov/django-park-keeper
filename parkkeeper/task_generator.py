# coding: utf-8
import multiprocessing
from time import sleep
import zmq

from django.conf import settings
from django.utils.timezone import now

from parkkeeper.event import emit_event
from parkkeeper import models
from parkworker.const import MONIT_TASK_EVENT


class TaskGenerator(multiprocessing.Process):
    context = None
    socket_pool = None

    def run(self):
        self.cancel_not_started_tasks()

        self.context = zmq.Context()
        self._create_pool()

        print('TaskGenerator started.')

        try:
            while True:
                tasks = models.MonitSchedule.create_tasks()
                for task in tasks:
                    task_json = task.to_json()
                    # task created event
                    emit_event(MONIT_TASK_EVENT, task_json)
                    # send monit tasks for workers
                    monit = models.Monit.objects.get(name=task.monit_name)
                    socket = self._get_socket(monit.worker_type)
                    # print('Send task', task.monit_name, 'on port', monit.worker_type.port)
                    socket.send_string(task_json)
                sleep(1)
        finally:
            for socket in self.socket_pool.values():
                socket.close()

    @staticmethod
    def cancel_not_started_tasks():
        models.MonitTask.objects\
            .filter(start_dt=None)\
            .update(cancel_dt=now(), cancel_reason='restart monit scheduler')

    def _create_pool(self):
        self.socket_pool = {}
        for worker_type in models.WorkerType.objects.all():
            self._create_socket(worker_type)

    def _get_socket(self, worker_type: models.WorkerType):
        if worker_type.name in self.socket_pool:
            return self.socket_pool[worker_type.name]
        else:
            return self._create_socket(worker_type)

    def _create_socket(self, worker_type: models.WorkerType):
        socket = self.context.socket(zmq.PUSH)
        socket.bind("tcp://*:%s" % worker_type.port)
        self.socket_pool[worker_type.name] = socket
        return socket
