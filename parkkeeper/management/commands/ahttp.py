# coding: utf-8
from django.core.management import BaseCommand

import asyncio
from aiohttp import web, MsgType


async def hello(request):
    return web.Response(body=b"Hello, world")

async def websocket_handler(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    while not ws.closed:
        msg = await ws.receive()

        if msg.tp == MsgType.text:
            if msg.data == 'close':
                await ws.close()
            else:
                ws.send_str(msg.data + '/answer')
        elif msg.tp == MsgType.close:
            print('websocket connection closed')
        elif msg.tp == MsgType.error:
            print('ws connection closed with exception %s' %
                  ws.exception())

    return ws

class Command(BaseCommand):
    help = 'Start aiohttp server'

    def handle(self, *args, **options):
        app = web.Application()
        app.router.add_route('GET', '/', hello)
        app.router.add_route('GET', '/ws_test', websocket_handler)

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

