# coding: utf-8
from abc import ABCMeta
import asyncio
import json
from aiohttp import web, MsgType
from django.conf import settings
from django.utils.timezone import now
from parkkeeper import models
from parkkeeper.event_publisher import EventPublisher, MONIT_STATUS_EVENT, MONIT_TASK_EVENT, MONIT_WORKER_EVENT


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
    app.router.add_route('GET', '/started_tasks', MonitStartedTaskHandler().get_handler)


class WebSocketHandler(metaclass=ABCMeta):
    ws = None
    stop_msg = 'close_ws'
    need_background = False
    stop_background_timeout = 1

    async def process_msg(self, msg_text):
        print(msg_text)


    async def background(self):
        while not self.ws.closed:
            print(now())
            await asyncio.sleep(1)
        print('Close background')


    async def get_handler(self, request):
        self.ws = web.WebSocketResponse()
        await self.ws.prepare(request)

        # start background process if needed
        background_task = None
        if self.need_background:
            loop = asyncio.get_event_loop()
            background_task = loop.create_task(self.background())

        # process ws messages
        while not self.ws.closed:
            await self._receive_msg()

        # stop background
        if background_task:
            background_task.cancel()

        return self.ws

    async def _receive_msg(self):
        msg = await self.ws.receive()

        if msg.tp == MsgType.text:
            if msg.data == self.stop_msg:
                print('Got stop msg')
                await self.ws.close()
            else:
                await self.process_msg(msg.data)
        elif msg.tp == MsgType.close:
            print('websocket connection closed')
        elif msg.tp == MsgType.error:
            print('ws connection closed with exception %s' %
                  self.ws.exception())


class MonitResultHandler(WebSocketHandler):
    need_background = True
    stop_background_timeout = 0.1

    async def background(self):
        while True:
            task_json = await EventPublisher.recv_event(MONIT_STATUS_EVENT)
            
            task = models.MonitTask.from_json(task_json)
            print('task', task)
            response = _get_task_represent(task)
            self.ws.send_str(json.dumps(response))


class MonitWaitingTaskHandler(WebSocketHandler):
    need_background = True
    stop_background_timeout = 0.1

    async def background(self):
        while True:
            response = {'waiting_tasks': []}
            waiting_tasks = models.MonitTask.get_waiting_tasks()
            for task in waiting_tasks:
                response['waiting_tasks'].append(_get_task_represent(task))
            print('waiting_tasks count', len(response['waiting_tasks']))

            self.ws.send_str(json.dumps(response))

            # waiting new events
            await EventPublisher.recv_event(MONIT_TASK_EVENT)


class MonitStartedTaskHandler(WebSocketHandler):
    need_background = True
    stop_background_timeout = 0.1

    async def background(self):
        while True:
            response = {'started_tasks': []}
            started_tasks = models.MonitTask.get_started_tasks()
            for task in started_tasks:
                response['started_tasks'].append(_get_task_represent(task))
            print('started_tasks count', len(response['started_tasks']))

            self.ws.send_str(json.dumps(response))

            # waiting new events
            await EventPublisher.recv_event(MONIT_WORKER_EVENT)


def _get_task_represent(task):
    return {
        'monit_name': task.monit_name,
        'host_address': task.host_address,
        'schedule_id': task.schedule_id,
        'result_dt': task.result.dt.isoformat(sep=' '),
        'extra': task.result.extra,
        'is_success': task.result.is_success,
    }