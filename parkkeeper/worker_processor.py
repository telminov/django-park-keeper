# coding: utf-8
import datetime
import json
import multiprocessing
import asyncio

from django.utils.timezone import now

from parkkeeper.event import get_sub_socket, async_recv_event
from parkkeeper.const import MONIT_WORKER_EVENT, MONIT_WORKER_HEART_BEAT_PERIOD
from parkkeeper import models
from parkkeeper.utils import dt_from_millis


class WorkerProcessor(multiprocessing.Process):
    subscriber_socket = None

    def run(self):
        self.cancel_dead_worker_tasks()

        self.subscriber_socket = get_sub_socket(MONIT_WORKER_EVENT)
        loop = asyncio.get_event_loop()
        try:
            loop.create_task(self.clear_dead_workers())
            loop.run_until_complete(self.get_event())
        finally:
            self.subscriber_socket.slose()
            loop.close()

    async def get_event(self):
        while True:
            msg = await async_recv_event(self.subscriber_socket)
            worker_data = json.loads(msg)
            print('WorkerProcessor get_event', msg)
            self._process_event(worker_data)

    @staticmethod
    async def clear_dead_workers():
        while True:
            dead_period = MONIT_WORKER_HEART_BEAT_PERIOD * 2
            dead_line = now() - datetime.timedelta(seconds=dead_period)
            dead = models.CurrentWorker.objects.filter(heart_beat_dt__lte=dead_line)
            if len(dead):
                print('Dead workers: ', len(dead), '. Removing...')
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
    def _process_event(worker_data: dict):
        worker_uuid = worker_data['main']['uuid']
        if 'stop_dt' in worker_data:
            models.CurrentWorker.objects.filter(main__uuid=worker_uuid).delete()
        else:
            created_dt = dt_from_millis(worker_data['main']['created_dt'])
            worker = models.Worker(
                uuid=worker_uuid,
                id=worker_data['main']['id'],
                created_dt=created_dt,
                host_name=worker_data['main']['host_name'],
            )

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

                # create not exists in db worker monits
                for monit_name in worker_data['monit_names']:
                    if not models.Monit.objects.filter(name=monit_name).exists():
                        models.Monit.objects.create(name=monit_name)

            models.CurrentWorker.objects.filter(main__uuid=worker_uuid).update(**update_params)