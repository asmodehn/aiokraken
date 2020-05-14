import asyncio
import functools
import os
from datetime import datetime

from bokeh.layouts import row
from bokeh.themes import Theme

from aiokraken.domain.models.ohlc import OHLC

from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken.domain.ohlcv import OHLCV
from aiokraken.rest import RestClient, Server

from bokeh.server.server import Server as BokehServer

# Fake background task I got from here:
# https://docs.python.org/3/library/asyncio-task.html#sleeping
async def display_date():
    while True:
        print(datetime.now())
        await asyncio.sleep(1)

def start_tornado(bkapp):
    # Server will take current runnin asyncio loop as his own.
    server = BokehServer({'/': bkapp})  # iolopp must remain to none, num_procs must be default (1)
    server.start()
    # app = make_app()
    # app.listen(8888)
    return server


def ohlc_page(doc, ohlc_1m: OHLC):

    p= ohlc_1m.plot(doc)  # pass the document to update

    doc.add_root(row(p, sizing_mode="scale_width"))
    doc.theme = Theme(filename=os.path.join(os.path.dirname(__file__), "theme.yaml"))

    # TODO : some way to close the ohlc subscription when we dont need it anymore...


async def main():

    print(f"Starting aiokraken...")

    # Client can be global: there is only one.
    rest = RestClient(server=Server())

    XBTUSD = (await rest.retrieve_assetpairs())['XBTUSD']

    # ohlc data can be global (one per market*timeframe only)
    # retrieving data (and blocking control flow)
    ohlc_1m = OHLCV(pair=XBTUSD, rest=rest)
    # TODO : use implicit retrieval (maybe by accessing slices of OHLC from bokeh doc/fig update??)

    bkgui_doc = functools.partial(ohlc_page, ohlc_1m=await ohlc_1m[KTimeFrameModel.one_minute]) # TODO : build a layout to explore different TF

    print(f"Starting Tornado Server...")
    server = start_tornado(bkapp=bkgui_doc)
    # Note : the bkapp is run for each request to the url...

    # bg task...
    asyncio.create_task(display_date())

    print('Serving Bokeh application on http://localhost:5006/')
    # server.io_loop.add_callback(server.show, "/")

    # THIS is already the loop that is currently running !!!
    assert server.io_loop.asyncio_loop == asyncio.get_running_loop(), f"{server.io_loop.asyncio_loop} != {asyncio.get_running_loop()}"
    # server.io_loop.start()  # DONT NEED !

    await asyncio.sleep(3600)  # running for one hour.
    # TODO : scheduling restart (crontab ? cli params ?) -> GOAL: ensure resilience (erlang-style)

asyncio.run(main())
