# coding: utf-8
import json

import zmq
from bson import json_util
from parkkeeper.datatools.task import process_task_data
from parkkeeper.base import StoppableMixin
from parkkeeper.event import get_sub_socket, async_recv_event
from parkworker.const import TASK_EVENT


class TaskResultCollector(StoppableMixin):
    def __init__(self, verbose: bool=False, sleep_period: float=0.1):
        super().__init__()
        self.context = zmq.Context()
        self.verbose = verbose
        self.sleep_period = sleep_period

    async def collect_tasks(self):
        if self.verbose:
            print('monitor_tasks start')
        subscriber_socket = get_sub_socket(TASK_EVENT, context=self.context)
        try:
            while not self.is_stopped():
                msg = await async_recv_event(subscriber_socket, self.is_stopped, self.sleep_period)
                if msg is None:
                    return

                data = json.loads(msg, object_hook=json_util.object_hook)
                process_task_data(data)
        finally:
            subscriber_socket.close()
