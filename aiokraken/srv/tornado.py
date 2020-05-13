import asyncio
import datetime
import tornado.ioloop
import tornado.web

from bokeh.server.server import Server

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

def start_tornado(bkapp):
    # Server will take current runnin asyncio loop as his own.
    server = Server({'/': bkapp})  # iolopp must remain to none, num_procs must be default (1)
    server.start()
    # app = make_app()
    # app.listen(8888)
    return server

