# coding: utf-8
import asyncio
import json
import multiprocessing
import zmq
from django.utils.timezone import now
from parkkeeper.event import get_sub_socket, async_recv_event
from parkkeeper import models
from parkkeeper.utils import dt_from_millis
from parkkeeper.worker_processor import WorkerProcessor
from parkworker.const import MONIT_TASK_EVENT


class TaskResultCollector(multiprocessing.Process):
    context = None

    def run(self):
        self.context = zmq.Context()
        loop = asyncio.get_event_loop()
        print('TaskResultCollector started.')
        try:
            loop.create_task(self.monitor_monit_tasks())
            loop.run_forever()
        finally:
            loop.close()

    async def monitor_monit_tasks(self) -> None:
        subscriber_socket = get_sub_socket(MONIT_TASK_EVENT, context=self.context)
        try:
            while True:
                msg = await async_recv_event(subscriber_socket)
                task_data = json.loads(msg)
                # print('TaskResultCollector monitor_monit_tasks', msg)
                self._process_monit_task(task_data)
        finally:
            subscriber_socket.close()

    @staticmethod
    def _process_monit_task(task_data: dict) -> None:
        update_params = {}
        if task_data.get('start_dt'):
            update_params['set__start_dt'] = dt_from_millis(task_data['start_dt'])

        if task_data.get('worker'):
            update_params['set__worker'] = WorkerProcessor.get_worker(worker_data=task_data['worker'])

        if task_data.get('result'):
            # print(task_data['result'])
            update_params['set__result'] = models.CheckResult(
                level=task_data['result']['level'],
                extra=task_data['result']['extra'],
                dt=dt_from_millis(task_data['result']['dt']),
            )
            TaskResultCollector._cancel_double(task_data)

        if update_params:
            task_id = task_data['_id']['$oid']
            models.MonitTask.objects.filter(id=task_id).update(**update_params)

    @staticmethod
    def _cancel_double(last_task_data) -> None:
        not_started = models.MonitTask.get_waiting_tasks().filter(
            schedule_id=last_task_data['schedule_id'],
            dc__lte=dt_from_millis(last_task_data['dc']['$date']),
        )
        not_started.update(cancel_dt=now(), cancel_reason='task not started and got result for more late same task')
