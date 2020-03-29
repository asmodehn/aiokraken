# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.1
#   kernelspec:
#     display_name: aiokraken
#     language: python
#     name: aiokraken
# ---

# +
import timecontrol
print(timecontrol.__file__) 

import aiokraken
print(aiokraken.__file__) 

from IPython.display import display
from IPython.core.debugger import set_trace

from aiokraken.rest.client import RestClient

# +
client = RestClient()

# set_trace()

display(await client.assets)
# -

await client.assetpairs

df = (await client.ohlc(pair="XBTEUR")).dataframe
df

# +

from bokeh.driving import count
from bokeh.layouts import column, gridplot, row
from bokeh.models import ColumnDataSource, Select, Slider
from bokeh.plotting import figure, show

# Useful Refs : 
# - https://docs.bokeh.org/en/latest/docs/user_guide/interaction/legends.html
# - https://docs.bokeh.org/en/latest/docs/gallery/candlestick.html
# - https://github.com/bokeh/bokeh/blob/master/examples/app/ohlc/main.py

from bokeh.io import output_notebook
output_notebook()


# +
from aiokraken.model.bokeh_figs.fig_ohlc import fig_ohlc

p = fig_ohlc(df=df)

show(p)


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
source = ColumnDataSource(df)
print(source)

#draw the same plot as before
show(p)


ws = WssClient(restclient=client)


# This is just a basic output test for websocket callback.
print(ws.loop)


def ws_callback(update):
#     print(update)
    dfup = update.to_tidfrow()
    dfup.reset_index(inplace=True)
    upd = dfup.to_dict( orient='list')
    #upd["datetime"]= [dt.to_pydatetime() for dt in upd["datetime"]]
    print(upd)
    source.stream(upd)


await ws.ohlc(["XBTEUR"], callback=ws_callback)


async def count(secs):
    for i in range(1,secs):
        #to help debug loop/display problems
        #print('.', end='', flush=True)
        await asyncio.sleep(1)

await count(60)

#TODO : some way to close the ohlc subscription to keep it in one cell...

