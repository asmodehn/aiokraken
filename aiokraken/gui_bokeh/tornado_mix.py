import asyncio
import datetime
import tornado.ioloop
import tornado.web

from bokeh.server.server import Server
from aiokraken.gui_bokeh.gui_ohlc import bkapp

# class MainHandler(tornado.web.RequestHandler):
#     def get(self):
#         self.write("Hello, world")
#
# def make_app():
#     return tornado.web.Application([
#         (r"/", MainHandler),
#     ])

# Fake background task I got from here:
# https://docs.python.org/3/library/asyncio-task.html#sleeping
async def display_date():
    while True:
        print(datetime.datetime.now())
        await asyncio.sleep(1)

async def start_tornado():
    # Server will take current runnin asyncio loop as his own.
    server = Server({'/': bkapp})  # iolopp must remain to none, num_proces must be default (1)
    server.start()
    # app = make_app()
    # app.listen(8888)
    return server

async def main():
    server = await start_tornado()
    asyncio.create_task(display_date())

    print('Opening Bokeh application on http://localhost:5006/')

    server.io_loop.add_callback(server.show, "/")
    # THIS is already the loop that is currently running !!!
    assert server.io_loop.asyncio_loop == asyncio.get_running_loop(), f"{server.io_loop.asyncio_loop} != {asyncio.get_running_loop()}"
    # server.io_loop.start()

    await asyncio.sleep(300)

asyncio.run(main())
