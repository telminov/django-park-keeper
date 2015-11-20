# coding: utf-8
import datetime
import json
import asyncio
import zmq
from bson import json_util
from django.conf import settings
from django.utils.timezone import now
from parkkeeper.base import StoppableMixin
from parkkeeper.datatools.task import cancel_dead_worker_tasks
from parkkeeper.event import get_sub_socket, async_recv_event
from parkkeeper import models
from parkworker.const import WORKER_EVENT, WORKER_HEART_BEAT_PERIOD
from parkkeeper.datatools.worker import process_worker_data


class WorkerProcessor(StoppableMixin):

    def __init__(self, verbose: bool=False, sleep_period=1):
        super().__init__()
        cancel_dead_worker_tasks()
        self.context = zmq.Context()
        self.verbose = verbose
        self.sleep_period = sleep_period

    async def process_workers(self):
        if self.verbose:
            print('process_workers started.')
        subscriber_socket = get_sub_socket(WORKER_EVENT, context=self.context)
        try:
            while not self.is_stopped():
                msg = await async_recv_event(subscriber_socket, self.is_stopped)
                if msg is None:
                    return

                worker_data = json.loads(msg, object_hook=json_util.object_hook)
                process_worker_data(worker_data)
        finally:
            subscriber_socket.close()

    async def register_workers(self):
        if self.verbose:
            print('register_workers start')

        registrator_socket = self.context.socket(zmq.REP)
        registrator_socket.bind("tcp://*:%s" % settings.ZMQ_WORKER_REGISTRATOR_PORT)

        try:
            while not self.is_stopped():
                try:
                    msg = registrator_socket.recv_string(flags=zmq.NOBLOCK)
                    worker_data = json.loads(msg, object_hook=json_util.object_hook)
                    if self.verbose:
                        print('register_workers %s %s %s' % (
                            worker_data['main']['host_name'],
                            worker_data['main']['id'],
                            worker_data['main']['type'],
                        ))

                    worker_type = models.WorkerType.create_if_not_exists(name=worker_data['main']['type'])
                    models.Monit.create_if_not_exists(worker_type, worker_data['monits'])
                    models.Work.create_if_not_exists(worker_type, worker_data['works'])

                    process_worker_data(worker_data)

                    answer_data = {'scheduler_port': worker_type.port}
                    answer_data_json = json.dumps(answer_data)
                    registrator_socket.send_string(answer_data_json)

                except zmq.error.Again:
                    pass
                await asyncio.sleep(self.sleep_period)
        finally:
            registrator_socket.close()

    async def clear_dead_workers(self):
        if self.verbose:
            print('clear_dead_workers start')
        while not self.is_stopped():
            dead_period = WORKER_HEART_BEAT_PERIOD * 2
            dead_line = now() - datetime.timedelta(seconds=dead_period)
            dead = models.CurrentWorker.objects.filter(heart_beat_dt__lte=dead_line)
            if len(dead):
                if self.verbose:
                    print('Dead workers: %s.' % len(dead), 'Removing...')
                dead.delete()
            await asyncio.sleep(self.sleep_period)


