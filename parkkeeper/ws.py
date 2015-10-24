# coding: utf-8
from abc import ABCMeta, abstractclassmethod
import asyncio
from aiohttp import web, MsgType

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
    app.router.add_route('GET', '/ws_test', MonitResultHandler().get_handler)



class WebSocketHandler(metaclass=ABCMeta):
    ws = None

    async def get_handler(self, request):
        self.ws = web.WebSocketResponse()
        await self.ws.prepare(request)

        while not self.ws.closed:
            msg = await self.ws.receive()

            if msg.tp == MsgType.text:
                self.process_msg(msg)
            elif msg.tp == MsgType.close:
                print('websocket connection closed')
            elif msg.tp == MsgType.error:
                print('ws connection closed with exception %s' %
                      self.ws.exception())

        return self.ws

    @abstractclassmethod
    def process_msg(self, msg):
        if msg.data == 'close':
            await self.ws.close()
        else:
            self.ws.send_str(msg.data + '/answer')



class MonitResultHandler(WebSocketHandler):
    def process_msg(self, msg):
        # TODO: subscribing on monitoring events
        # zmq.NOBLOCK
        self.ws.send_str('{"message": "test"}')