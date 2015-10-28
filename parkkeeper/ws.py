# coding: utf-8
from abc import ABCMeta, abstractclassmethod
import asyncio
import json
from aiohttp import web, MsgType
from django.utils.timezone import now
from parkkeeper import models
import zmq

def start_server():
    app = web.Application()
    add_routes(app)

    loop = asyncio.get_event_loop()
    handler = app.make_handler()
    f = loop.create_server(handler, '0.0.0.0', 8080)
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

    async def background(self):
        context = zmq.Context()
        subscriber_socket = context.socket(zmq.SUB)
        subscriber_socket.connect("tcp://localhost:5561")
        subscriber_socket.setsockopt(zmq.SUBSCRIBE, b'')

        try:
            while not self.ws.closed:
                print(now().isoformat())
                try:
                    task_json = subscriber_socket.recv_json(flags=zmq.NOBLOCK)
                    task = models.MonitTask.from_json(task_json)
                    print(task)
                    response = {
                        'monit_name': task.monit_name,
                        'host_address': task.host_address,
                        'schedule_id': task.schedule_id,
                        'result_dt': task.result.dt.isoformat(sep=' '),
                        'extra': task.result.extra,
                        'is_success': task.result.is_success,
                    }
                    self.ws.send_str(json.dumps(response))
                except zmq.error.Again:
                    pass
                await asyncio.sleep(0.5)
        finally:
            subscriber_socket.close()
            context.term()