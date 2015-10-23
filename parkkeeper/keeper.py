# coding: utf-8
from multiprocessing import Process, Queue
from time import sleep
import uuid
import random

class Keeper:
    STOP_MSG = 'STOP'

    def __init__(self, monits_count=2):
        self.monit_workers_count = monits_count
        self.monit_workers = []
        self.monit_queue = Queue()

    def start_loop(self):
        self._start_monits()

        try:
            while True:
                for w in self._get_alive_monit_workers():
                    task = str(random.randint(1, 100))
                    self.monit_queue.put(task)

                sleep(1)
        finally:
            print('Stop them all!..')
            self._stop_workers()
            sleep(1)

    def _start_monits(self):
        for worker_id in range(0, self.monit_workers_count):
            monit_worker = MonitWorker()
            monit_worker.setup(self.monit_queue, worker_id=str(worker_id))
            monit_worker.start()
            self.monit_workers.append(monit_worker)

    def _stop_workers(self):
        for w in self._get_alive_monit_workers():
            self.monit_queue.put(self.STOP_MSG)

    def _get_alive_monit_workers(self):
        return [w for w in self.monit_workers if w.is_alive()]

class MonitWorker(Process):
    worker_id = None
    task_queue = None

    def setup(self, task_queue: Queue, worker_id: str=None):
        self.worker_id = worker_id or str(uuid.uuid4())
        self.task_queue = task_queue

    def run(self):
        print('working %s started' % self.worker_id)

        while True:
            task = self.task_queue.get()
            sleep(0.5)

            if task == Keeper.STOP_MSG:
                print('working %s stopped' % self.worker_id)
                break

            print('monit %s working: %s...' % (self.worker_id, task))
