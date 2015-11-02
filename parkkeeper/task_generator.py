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

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.bind("tcp://*:%s" % settings.ZMQ_MONIT_SCHEDULER_PORT)
        print('TaskGenerator started.')

        self.cancel_not_started_tasks()

        while True:
            tasks = models.MonitSchedule.create_tasks()
            for task in tasks:
                task_json = task.to_json()
                # task created event
                emit_event(MONIT_TASK_EVENT, task_json)
                # send monit tasks for workers
                socket.send_json(task_json)
            sleep(1)

    @staticmethod
    def cancel_not_started_tasks():
        models.MonitTask.objects\
            .filter(start_dt=None)\
            .update(cancel_dt=now(), cancel_reason='restart monit scheduler')
