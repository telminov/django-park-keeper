# coding: utf-8
import datetime
import json
import multiprocessing
import asyncio
import zmq
from django.conf import settings
from django.utils.timezone import now

from parkkeeper.event import get_sub_socket, async_recv_event
from parkkeeper import models
from parkkeeper.utils import dt_from_millis
from parkworker.const import MONIT_WORKER_EVENT, MONIT_WORKER_HEART_BEAT_PERIOD


class WorkerProcessor(multiprocessing.Process):
    context = None

    def run(self):
        self.cancel_dead_worker_tasks()
        self.context = zmq.Context()
        loop = asyncio.get_event_loop()
        print('WorkerProcessor started.')
        try:
            loop.create_task(self.clear_dead_workers())
            loop.create_task(self.register_workers())
            loop.create_task(self.monitor_workers())
            loop.run_forever()
        finally:
            loop.close()

    async def monitor_workers(self):
        subscriber_socket = get_sub_socket(MONIT_WORKER_EVENT, context=self.context)
        try:
            while True:
                msg = await async_recv_event(subscriber_socket)
                worker_data = json.loads(msg)
                # print('WorkerProcessor monitor_workers', msg)
                self._process_worker_state(worker_data)
        finally:
            subscriber_socket.close()

    async def register_workers(self):
        registrator_socket = self.context.socket(zmq.REP)
        registrator_socket.bind("tcp://*:%s" % settings.ZMQ_WORKER_REGISTRATOR_PORT)

        try:
            while True:
                try:
                    msg = registrator_socket.recv_string(flags=zmq.NOBLOCK)
                    worker_data = json.loads(msg)
                    print('register_workers', msg)

                    # create worker type in not exists
                    worker_type = models.WorkerType.create_if_not_exists(name=worker_data['main']['type'])

                    # create not exists in db worker monits
                    for monit_name in worker_data['monit_names']:
                        if not models.Monit.objects.filter(name=monit_name).exists():
                            models.Monit.objects.create(
                                name=monit_name,
                                worker_type=worker_type,
                            )

                    self._process_worker_state(worker_data)

                    answer_data = {'monit_scheduler_port': worker_type.port}
                    answer_data_json = json.dumps(answer_data)
                    registrator_socket.send_string(answer_data_json)

                except zmq.error.Again:
                    pass
                await asyncio.sleep(1)
        finally:
            registrator_socket.close()

    @staticmethod
    async def clear_dead_workers():
        while True:
            dead_period = MONIT_WORKER_HEART_BEAT_PERIOD * 2
            dead_line = now() - datetime.timedelta(seconds=dead_period)
            dead = models.CurrentWorker.objects.filter(heart_beat_dt__lte=dead_line)
            if len(dead):
                print('Dead workers: %s.' % len(dead), 'Removing...')
                dead.delete()
            await asyncio.sleep(dead_period)

    @staticmethod
    def cancel_dead_worker_tasks():
        current_worker_uuids = models.CurrentWorker.objects.values_list('main__uuid')
        models.MonitTask.objects\
            .filter(start_dt__ne=None, result__dt=None, cancel_dt=None,
                    worker__uuid__not__in=current_worker_uuids)\
            .update(cancel_dt=now(), cancel_reason='monit worker not alive')

    @staticmethod
    def get_worker(worker_data: dict):
        created_dt = dt_from_millis(worker_data['created_dt'])
        worker = models.Worker(
            uuid=worker_data['uuid'],
            id=worker_data['id'],
            created_dt=created_dt,
            host_name=worker_data['host_name'],
            type=worker_data['type'],
        )
        return worker

    @classmethod
    def _process_worker_state(cls, worker_data: dict):
        worker_uuid = worker_data['main']['uuid']
        if 'stop_dt' in worker_data:
            models.CurrentWorker.objects.filter(main__uuid=worker_uuid).delete()
        else:
            worker = cls.get_worker(worker_data['main'])

            heart_beat_dt = dt_from_millis(worker_data['heart_beat_dt'])
            update_params = {
                'set__main': worker,
                'set__heart_beat_dt': heart_beat_dt,
                'upsert': True,
            }

            if 'tasks' in worker_data:
                update_params['set__task_ids'] = worker_data['tasks']

            if 'monit_names' in worker_data:
                update_params['set__monit_names'] = worker_data['monit_names']

            models.CurrentWorker.objects.filter(main__uuid=worker_uuid).update(**update_params)

