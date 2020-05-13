import asyncio
import functools

from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken import OHLC
from aiokraken.rest import RestClient, Server

from aiokraken.srv.tornado import start_tornado, display_date
from aiokraken.srv.gui import bkgui


async def main():

    print(f"Starting aiokraken...")

    # Client can be global: there is only one.
    rest = RestClient(server=Server())

    # ohlc data can be global (one per market*timeframe only)
    ohlc_1m = OHLC(pair='XBTUSD', timeframe=KTimeFrameModel.one_minute, restclient=rest)

    # retrieving data (and blocking control flow)
    # TODO : use implicit retrieval (maybe by accessing slices of OHLC from bokeh doc/fig update??)
    await ohlc_1m()

    bkgui_doc = functools.partial(bkgui, ohlc_1m=ohlc_1m)

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

    await asyncio.sleep(300)

asyncio.run(main())
