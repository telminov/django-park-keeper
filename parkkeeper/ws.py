# coding: utf-8
from abc import ABCMeta
import asyncio
import json
from aiohttp import web, MsgType
from django.conf import settings
from django.utils.timezone import now
from parkkeeper import models
from parkkeeper.event import async_recv_event, get_sub_socket
from parkkeeper.utils import dt_from_millis
from parkworker.const import MONIT_STATUS_EVENT, MONIT_TASK_EVENT, MONIT_WORKER_EVENT


def start_server():
    app = web.Application()
    add_routes(app)

    loop = asyncio.get_event_loop()
    handler = app.make_handler()
    f = loop.create_server(handler, '0.0.0.0', settings.WEB_SOCKET_SERVER_PORT)
    srv = loop.run_until_complete(f)
    print('serving on', srv.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(handler.finish_connections(1.0))
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(app.finish())
    loop.close()


def add_routes(app):
    app.router.add_route('GET', '/monits', MonitResultHandler().get_handler)
    app.router.add_route('GET', '/waiting_tasks', MonitWaitingTaskHandler().get_handler)
    app.router.add_route('GET', '/current_workers', MonitCurrentWorkerHandler().get_handler)


class WebSocketHandler(metaclass=ABCMeta):
    stop_msg = 'close_ws'
    need_background = False
    stop_background_timeout = 1

    async def process_msg(self, msg_text: str):
        print(msg_text)

    async def background(self, ws: web.WebSocketResponse):
        while not ws.closed:
            print(now())
            await asyncio.sleep(1)
        print('Close background')

    async def get_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # start background process if needed
        background_task = None
        if self.need_background:
            loop = asyncio.get_event_loop()
            background_task = loop.create_task(self.background(ws))

        # process ws messages
        while not ws.closed:
            await self._receive_msg(ws)

        # stop background
        if background_task:
            background_task.cancel()

        return ws

    async def _receive_msg(self, ws: web.WebSocketResponse):
        msg = await ws.receive()

        if msg.tp == MsgType.text:
            if msg.data == self.stop_msg:
                print('Got stop msg')
                await ws.close()
            else:
                await self.process_msg(msg.data)
        elif msg.tp == MsgType.close:
            print('websocket connection closed')
        elif msg.tp == MsgType.error:
            print('ws connection closed with exception %s' %
                  ws.exception())


class MonitResultHandler(WebSocketHandler):
    need_background = True
    stop_background_timeout = 0.1

    async def background(self, ws):
        subscriber_socket = get_sub_socket(MONIT_STATUS_EVENT)
        try:
            while True:
                task_json = await async_recv_event(subscriber_socket)

                task = models.MonitTask.from_json(task_json)
                # print('task', task)
                response = _get_task_represent(task)
                ws.send_str(json.dumps(response))
        finally:
            subscriber_socket.close()


class MonitWaitingTaskHandler(WebSocketHandler):
    need_background = True
    stop_background_timeout = 0.1

    async def background(self, ws):
        subscriber_socket = get_sub_socket(MONIT_TASK_EVENT)
        try:
            while True:
                response = {'waiting_tasks': []}
                waiting_tasks = models.MonitTask.get_waiting_tasks()
                for task in waiting_tasks:
                    response['waiting_tasks'].append(_get_task_represent(task))
                # print('waiting_tasks count', len(response['waiting_tasks']))

                ws.send_str(json.dumps(response))

                # waiting new events
                await async_recv_event(subscriber_socket)
        finally:
            subscriber_socket.close()


class MonitCurrentWorkerHandler(WebSocketHandler):
    need_background = True
    stop_background_timeout = 0.1

    async def background(self, ws):
        subscriber_socket = get_sub_socket(MONIT_WORKER_EVENT)
        try:
            while True:
                response = {'current_workers': []}
                workers = models.CurrentWorker.objects.all()
                for worker in workers:
                    response['current_workers'].append(
                        _get_worker_represent(worker)
                    )
                # print('current_workers count', len(response['current_workers']))

                ws.send_str(json.dumps(response))

                # waiting new events
                await async_recv_event(subscriber_socket)
        finally:
            subscriber_socket.close()


def _get_worker_represent(worker):
    worker_data = {
        'uuid': str(worker.main.uuid),
        'id': worker.main.id,
        'created_dt': worker.main.created_dt.isoformat(sep=' '),
        'host_name': worker.main.host_name,
        'tasks': [],
    }

    for task in worker.get_tasks():
        task_data = _get_task_represent(task)
        worker_data['tasks'].append(task_data)

    return worker_data


def _get_task_represent(task):
    task_data = {
        'id': str(task.id),
        'monit_name': task.monit_name,
        'host_address': task.host_address,
        'schedule_id': task.schedule_id,
        'start_dt': None,
        'result_dt': None,
        'extra': None,
        'level': None,
        'worker': None,
    }

    if task.start_dt:
        if isinstance(task.start_dt, int):
            task.start_dt = dt_from_millis(task.start_dt)
        task_data['start_dt'] = task.start_dt.isoformat(sep=' ')

    if task.result:
        if isinstance(task.result.dt, int):
            task.result.dt = dt_from_millis(task.result.dt)
        task_data['result_dt'] = task.result.dt.isoformat(sep=' ')
        task_data['extra'] = task.result.extra
        task_data['level'] = task.result.level

    if task.worker:
        if isinstance(task.worker.created_dt, int):
            task.worker.created_dt = dt_from_millis(task.worker.created_dt)
        task_data['worker'] = {
            'uuid': str(task.worker.uuid),
            'id': task.worker.id,
            'created_dt': task.worker.created_dt.isoformat(sep=' '),
            'host_name': task.worker.host_name,
        }

    return task_data
