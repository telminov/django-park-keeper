# coding: utf-8
from abc import ABCMeta
import asyncio
import json
from aiohttp import web, MsgType
from bson import json_util
from django.conf import settings
from django.utils.timezone import now
from parkkeeper import models
from parkkeeper.event import async_recv_event, get_sub_socket
from parkkeeper.const import MONIT_SCHEDULE_EVENT, WORK_SCHEDULE_EVENT
from parkworker.const import MONIT_STATUS_EVENT, TASK_EVENT, WORKER_EVENT, WORK_STATUS_EVENT


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
    app.router.add_route('GET', '/monit_schedules', MonitSchedulesHandler().get_handler)
    app.router.add_route('GET', '/work_schedules', WorkSchedulesHandler().get_handler)
    app.router.add_route('GET', '/monits', MonitResultHandler().get_handler)
    app.router.add_route('GET', '/works', MonitResultHandler().get_handler)
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


class MonitSchedulesHandler(WebSocketHandler):
    need_background = True
    stop_background_timeout = 0.1

    async def background(self, ws):
        subscriber_socket = get_sub_socket(MONIT_SCHEDULE_EVENT)
        try:
            while True:
                monit_schedule_json = await async_recv_event(subscriber_socket)
                # print('monit_schedule', monit_schedule_json)
                ws.send_str(monit_schedule_json)
        finally:
            subscriber_socket.close()


class WorkSchedulesHandler(WebSocketHandler):
    need_background = True
    stop_background_timeout = 0.1

    async def background(self, ws):
        subscriber_socket = get_sub_socket(WORK_SCHEDULE_EVENT)
        try:
            while True:
                work_schedule_json = await async_recv_event(subscriber_socket)
                # print('work_schedule', work_schedule_json)
                ws.send_str(work_schedule_json)
        finally:
            subscriber_socket.close()


class MonitResultHandler(WebSocketHandler):
    need_background = True
    stop_background_timeout = 0.1

    async def background(self, ws):
        subscriber_socket = get_sub_socket(MONIT_STATUS_EVENT)
        try:
            while True:
                task_json = await async_recv_event(subscriber_socket)
                task_data = json.loads(task_json, object_hook=json_util.object_hook)
                response = _get_task_represent(task_data)
                ws.send_str(json.dumps(response, default=json_util.default))
        finally:
            subscriber_socket.close()


class WorkResultHandler(WebSocketHandler):
    need_background = True
    stop_background_timeout = 0.1

    async def background(self, ws):
        subscriber_socket = get_sub_socket(WORK_STATUS_EVENT)
        try:
            while True:
                task_json = await async_recv_event(subscriber_socket)
                task_data = json.loads(task_json, object_hook=json_util.object_hook)
                response = _get_task_represent(task_data)
                ws.send_str(json.dumps(response, default=json_util.default))
        finally:
            subscriber_socket.close()


class MonitWaitingTaskHandler(WebSocketHandler):
    need_background = True
    stop_background_timeout = 0.1

    async def background(self, ws):
        subscriber_socket = get_sub_socket(TASK_EVENT)
        try:
            while True:
                response = {'waiting_tasks': []}
                waiting_tasks = models.MonitTask.get_waiting_tasks()
                for task in waiting_tasks:
                    task_data = task.get_data()['task']
                    response['waiting_tasks'].append(_get_task_represent(task_data))
                # print('waiting_tasks count', len(response['waiting_tasks']))

                ws.send_str(json.dumps(response, default=json_util.default))

                # waiting new events
                await async_recv_event(subscriber_socket)
        finally:
            subscriber_socket.close()


class MonitCurrentWorkerHandler(WebSocketHandler):
    need_background = True
    stop_background_timeout = 0.1

    async def background(self, ws):
        subscriber_socket = get_sub_socket(WORKER_EVENT)
        try:
            while True:
                response = {'current_workers': []}
                workers = models.CurrentWorker.objects.all()
                for worker in workers:
                    response['current_workers'].append(
                        _get_worker_represent(worker)
                    )
                # print('current_workers count', len(response['current_workers']))

                # print(response)
                ws.send_str(json.dumps(response, default=json_util.default))

                # waiting new events
                await async_recv_event(subscriber_socket)
        finally:
            subscriber_socket.close()


def _get_worker_represent(worker: models.CurrentWorker) -> dict:
    worker_data = {
        'uuid': str(worker.main.uuid),
        'id': worker.main.id,
        'created_dt': worker.main.created_dt.isoformat(sep=' '),
        'host_name': worker.main.host_name,
        'type': worker.main.type,
        'tasks': [],
    }

    for task in worker.get_tasks():
        task_data = _get_task_represent(task.get_data()['task'])
        worker_data['tasks'].append(task_data)

    return worker_data


def _get_task_represent(task: dict) -> dict:
    task_data = {
        'id': task['id'],
        'host_address': task['host_address'],
        'schedule_id': task['schedule_id'],
        'start_dt': None,
        'result_dt': None,
        'extra': None,
        'level': None,
        'worker': None,
    }

    if 'monit_name' in task:
        task_data['monit_name'] = task['monit_name'],

    if 'work_name' in task:
        task_data['work_name'] = task['work_name'],

    if 'start_dt' in task:
        task_data['start_dt'] = task['start_dt'].replace(microsecond=0).isoformat(sep=' ')

    if 'result' in task:
        task_data['result_dt'] = task['result']['dt'].replace(microsecond=0).isoformat(sep=' ')
        task_data['extra'] = task['result']['extra']
        task_data['level'] = task['result']['level']

    if 'worker' in task:
        task_data['worker'] = task['worker']
        task_data['worker']['created_dt'] = task['worker']['created_dt'].replace(microsecond=0).isoformat(sep=' ')

    return task_data
