# TODO : some GUI for all aiokraken things to watch over time...
import functools

from IPython.display import display
from IPython.core.debugger import set_trace
from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken import OHLC
from aiokraken.rest.client import RestClient

client = RestClient()

from bokeh.layouts import column, gridplot, row
from bokeh.models import ColumnDataSource, Select, Slider
from bokeh.plotting import figure, show

# Useful Refs :
# - https://docs.bokeh.org/en/latest/docs/user_guide/interaction/legends.html
# - https://docs.bokeh.org/en/latest/docs/gallery/candlestick.html
# - https://github.com/bokeh/bokeh/blob/master/examples/app/ohlc/main.py

from bokeh.io import curdoc

from aiokraken.model.bokeh_figs.fig_ohlc import fig_ohlc
#
# p = fig_ohlc(df=df)
p=None


# +
import pandas as pd
from aiokraken.websockets.client import WssClient
from datetime import timedelta
import asyncio

# extra instructions to follow the end of the x range
# p.x_range.follow = "end"
# p.x_range.follow_interval = pd.Timedelta(minutes=720)
# p.x_range.range_padding = pd.Timedelta(minutes=1)

# use a ColumnDataSource to get the stream method (on top of existing panda dataframe)
# source = ColumnDataSource(df)
# print(source)


# this must only be modified from a Bokeh session callback
source = None

# This is important! Save curdoc() to make sure all threads
# see the same document.
doc = curdoc()


# TODO : REST request first.
doc.title = "OHLC"



import asyncio
from aiokraken.rest.client import RestClient
from aiokraken.rest.api import Server

# Client can be global: there is only one.
rest = RestClient(server=Server())

# ohlc data can be global (one per market*timeframe only)
ohlc_1m = OHLC(pair='ETHEUR', timeframe=KTimeFrameModel.one_minute, restclient=rest)

loop = asyncio.get_event_loop()

# TODO : somehow link the aiokraken LOG to some console in the webpage...

# in sync with the doc update loop
def ohlc_widget_update(upd):
    source.stream(upd)


# in sync with the doc update loop
def ohlc_widget(p):
    doc.add_root(row(p, sizing_mode="scale_width"))


def ws_callback(update):
#     print(update)
    dfup = update.to_tidfrow()
    dfup.reset_index(inplace=True)
    upd = dfup.to_dict( orient='list')
    #upd["datetime"]= [dt.to_pydatetime() for dt in upd["datetime"]]
    print(upd)
    # finally scheduling for doc addition at next tick
    doc.add_next_tick_callback(functools.partial(ohlc_widget_update, upd))


async def ohlc_watcher():

    global p, source
    # we need an async def here to allow "pausing" in the flow (await), and wait for ohlc updates

    await ohlc_1m()

    df = ohlc_1m.model.dataframe

    # for display
    source = ColumnDataSource(df)
    p = fig_ohlc(df=df)

    # finally scheduling for doc addition at next tick
    doc.add_next_tick_callback(functools.partial(ohlc_widget, p))

    # adding websocket callback via decorator
    ohlc_1m.callback(ws_callback)

# chosing to integrate this task in the current running loop (and not another thread)
loop.create_task(ohlc_watcher())


# TODO : some way to close the ohlc subscription when we dont need it anymore...


