# coding: utf-8
from abc import ABCMeta, abstractclassmethod
import asyncio
import json
from aiohttp import web, MsgType
from django.utils.timezone import now
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

    async def get_handler(self, request):
        self.ws = web.WebSocketResponse()
        await self.ws.prepare(request)

        while not self.ws.closed:
            msg = await self.ws.receive()

            if msg.tp == MsgType.text:
                await self.process_msg(msg)
            elif msg.tp == MsgType.close:
                print('websocket connection closed')
            elif msg.tp == MsgType.error:
                print('ws connection closed with exception %s' %
                      self.ws.exception())

        return self.ws

    @abstractclassmethod
    async def process_msg(self, msg):
        if msg.data == 'close':
            await self.ws.close()
        else:
            self.ws.send_str(msg.data + '/answer')


class MonitResultHandler(WebSocketHandler):
    async def process_msg(self, msg):
        context = zmq.Context()
        subscriber_socket = context.socket(zmq.SUB)
        subscriber_socket.connect("tcp://localhost:5561")
        subscriber_socket.setsockopt(zmq.SUBSCRIBE, b'')

        try:
            while True:
                print(now().isoformat())
                try:
                    status = subscriber_socket.recv_json(flags=zmq.NOBLOCK)
                    print(status)
                    self.ws.send_str(json.dumps(status))
                except zmq.error.Again:
                    pass
                await asyncio.sleep(1)
        finally:
            subscriber_socket.close()
            context.term()