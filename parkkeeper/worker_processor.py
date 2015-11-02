# coding: utf-8
import datetime
import json
import multiprocessing
import asyncio

import pytz
from django.utils.timezone import now

from parkkeeper.event import get_sub_socket, recv_event, async_recv_event
from parkkeeper.const import MONIT_WORKER_EVENT
from parkkeeper import models


class WorkerProcessor(multiprocessing.Process):

    # def run(self):
    #     # TODO: add to hear beats processing
    #     self.cancel_dead_worker_tasks()
    #
    #     loop = asyncio.get_event_loop()
    #     while True:
    #         loop.run_until_complete(self.get_event())
    #     loop.close()
    #
    # def _process_event(self, worker_data):
    #     pass
    #
    # async def get_event(self):
    #     msg = await async_recv_event(MONIT_WORKER_EVENT)
    #     print('WorkerProcessor get_event', msg)
    #     self._process_event(msg)

    def run(self):
        # TODO: add to hear beats processing
        self.cancel_dead_worker_tasks()

        subscriber_socket = get_sub_socket(MONIT_WORKER_EVENT)
        try:
            while True:
                msg = recv_event(subscriber_socket)
                worker_data = json.loads(msg)
                print('WorkerProcessor get_event', msg)
                self._process_event(worker_data)
        finally:
            subscriber_socket.close()

    @staticmethod
    def _process_event(worker_data: dict):
        worker_uuid = worker_data['uuid']
        if worker_data['delete_dt']:
            models.CurrentWorker.objects.filter(info__uuid=worker_uuid).delete()
        else:
            created_dt = datetime.datetime.fromtimestamp(worker_data['created_dt']/1000.0).replace(tzinfo=pytz.utc)
            worker = models.Worker(
                uuid=worker_uuid,
                id=str(worker_data['id']),
                created_dt=created_dt,
                host_name=worker_data['host_name'],
                monit_names=worker_data['monit_names'],
            )

            models.CurrentWorker.objects.filter(info__uuid=worker_uuid).update(
                set__info=worker,
                set__task_ids=worker_data['tasks'],
                upsert=True
            )

            # create not exists in db worker monits
            for monit_name in worker.monit_names:
                if not models.Monit.objects.filter(name=monit_name).exists():
                    models.Monit.objects.create(name=monit_name)

    @staticmethod
    def cancel_dead_worker_tasks():
        current_worker_uuids = models.CurrentWorker.objects.values_list('info__uuid')
        models.MonitTask.objects\
            .filter(start_dt__ne=None, result__dt=None, cancel_dt=None,
                    worker__uuid__not__in=current_worker_uuids)\
            .update(cancel_dt=now(), cancel_reason='monit worker not alive')

