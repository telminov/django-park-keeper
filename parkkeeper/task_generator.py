# coding: utf-8
import asyncio
from typing import Dict, List
import zmq
from parkkeeper.base import StoppableMixin
from parkkeeper.event import emit_event
from parkkeeper import models
from parkworker.const import TASK_EVENT, FRESH_TASK_CANCEL_REASON, TASK_GENERATOR_RESTART_CANCEL_REASON


class TaskGenerator(StoppableMixin):

    def __init__(self, verbose: bool=False, sleep_period=1):
        super().__init__()
        self.cancel_not_started_tasks()
        self.tasks = TaskQueue()
        self.context = zmq.Context()
        self.verbose = verbose
        self.sleep_period = sleep_period

    @staticmethod
    def cancel_not_started_tasks():
        models.MonitTask.cancel_not_started(reason=TASK_GENERATOR_RESTART_CANCEL_REASON)
        models.WorkTask.cancel_not_started(reason=TASK_GENERATOR_RESTART_CANCEL_REASON)

    async def generate_monit_tasks(self):
        if self.verbose:
            print('generate_monit_tasks start')
        while not self.is_stopped():
            for task in models.MonitSchedule.create_tasks():
                assert isinstance(task, models.MonitTask)
                task_json = task.get_json()
                emit_event(TASK_EVENT, task_json)
                self.tasks.add_task(task)
            await asyncio.sleep(self.sleep_period)

    async def generate_work_tasks(self):
        if self.verbose:
            print('generate_work_tasks start')
        while not self.is_stopped():
            for task in models.WorkSchedule.create_tasks():
                assert isinstance(task, models.WorkTask)
                task_json = task.get_json()
                emit_event(TASK_EVENT, task_json)
                self.tasks.add_task(task)
            await asyncio.sleep(self.sleep_period)

    async def push_tasks(self):
        if self.verbose:
            print('push_tasks start')
        self._create_pool()
        try:
            while not self.is_stopped():
                for worker_type, tasks in self.tasks.get_tasks_by_worker_type().items():
                    self._push_for_workers(worker_type, tasks)
                await asyncio.sleep(0.1)
        finally:
            self._close_pool()

    def _push_for_workers(self, worker_type: str, tasks: List[models.BaseTask]):
        try:
            for task in tasks:
                worker_type = task.get_worker_type()
                socket = self._get_socket(worker_type)
                socket.send_string(task.get_json(), flags=zmq.NOBLOCK)
                self.tasks.rm_task(task)

        # if no workers for pulling tasks
        except zmq.Again:
            return

    def _create_pool(self):
        self._socket_pool = {}
        for worker_type in models.WorkerType.objects.all():
            self._create_socket(worker_type)

    def _close_pool(self):
        for socket in self._socket_pool.values():
            socket.close()

    def _get_socket(self, worker_type: models.WorkerType):
        if worker_type.name in self._socket_pool:
            return self._socket_pool[worker_type.name]
        else:
            return self._create_socket(worker_type)

    def _create_socket(self, worker_type: models.WorkerType):
        socket = self.context.socket(zmq.PUSH)
        socket.bind("tcp://*:%s" % worker_type.port)
        self._socket_pool[worker_type.name] = socket
        return socket


class TaskQueue:
    def __init__(self):
        self.tasks = {}

    def add_task(self, task: models.BaseTask):
        worker_type = task.get_worker_type().name
        key = self._get_key(task)

        if key in self.tasks.setdefault(worker_type, {}):
            old_task = self.tasks[worker_type].pop(key)
            self._cancel_task(old_task)

        self.tasks[worker_type][key] = task

    def rm_task(self, task: models.BaseTask):
        worker_type = task.get_worker_type().name
        key = self._get_key(task)
        self.tasks[worker_type].pop(key)

    def get_tasks_by_worker_type(self) -> Dict[str, List[models.BaseTask]]:
        tasks = {}
        for worker_type, tasks_dict in self.tasks.items():
            tasks.setdefault(worker_type, []).extend(tasks_dict.values())
        return tasks

    @staticmethod
    def _get_key(task: models.BaseTask):
        return task.get_task_type(), task.host_address, task.get_name()

    @staticmethod
    def _cancel_task(task: models.BaseTask):
        task.cancel_not_started(task_pk=task.pk, reason=FRESH_TASK_CANCEL_REASON)
        task_json = type(task).objects.get(pk=task.pk).get_json()
        emit_event(TASK_EVENT, task_json)

