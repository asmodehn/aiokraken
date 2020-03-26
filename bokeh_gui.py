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

source = (await client.ohlc(pair="XBTEUR")).dataframe
source

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

TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
# -

p = figure(plot_height=240, tools=TOOLS, x_axis_type="datetime", y_axis_location="right")
# p.x_range.follow = "end"
# p.x_range.follow_interval = 100
# p.x_range.range_padding = 0

# +

#p.line(x='datetime', y='vwap', line_width=1, color='navy', source=source)

p.segment(x0='datetime', y0='low', x1='datetime', y1='high', line_width=1, color='black', source=source)

inc = source.open < source.close
dec = source.close > source.open
w = source.index[1] - source.index[0]  # width is one index step

p.vbar(x=source.index[inc],width=w, bottom=source.open[inc], top=source.close[inc], fill_color="#D5E1DD", line_color="black")
p.vbar(x=source.index[dec],width=w, top=source.open[dec], bottom=source.close[dec], fill_color="#F2583E", line_color="black")

show(p)
