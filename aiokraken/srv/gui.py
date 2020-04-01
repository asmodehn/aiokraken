# TODO : some GUI for all aiokraken things to watch over time...
import functools

# IMPORTANT : This code is run for **every client connection**
# => it should not have any blocking function call, and run things in one pass...
import os

from IPython.display import display
from IPython.core.debugger import set_trace
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
from bokeh.themes import Theme

from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken import OHLC
from aiokraken.rest.client import RestClient

from bokeh.layouts import column, gridplot, row
from bokeh.models import ColumnDataSource, Select, Slider
from bokeh.plotting import figure, show

# Useful Refs :
# - https://docs.bokeh.org/en/latest/docs/user_guide/interaction/legends.html
# - https://docs.bokeh.org/en/latest/docs/gallery/candlestick.html
# - https://github.com/bokeh/bokeh/blob/master/examples/app/ohlc/main.py


from aiokraken.model.bokeh_figs.fig_ohlc import fig_ohlc


# TODO : somehow link the aiokraken LOG to some console in the webpage...


def bkgui(doc, ohlc_1m):
    df = ohlc_1m.model.dataframe

    # for display
    source = ColumnDataSource(df)
    p = fig_ohlc(df=df)

    # def ohlc_widget_update(upd):
    #     source.stream(upd)  #BUG : NOT WORKING !!!!

    def ws_callback(update):
        #     print(update)
        dfup = update.to_tidfrow()
        print(dfup.head())

        source.stream(dfup)
        # finally scheduling for doc addition at next tick (when document is unlocked)
        # doc.add_next_tick_callback(functools.partial(ohlc_widget_update, dfup))

    doc.add_root(row(p, sizing_mode="scale_width"))

    # finally scheduling for doc addition at next tick (when document is unlocked)
    # doc.add_next_tick_callback(functools.partial(ohlc_widget, p))

    # adding callback for this channel via decorator method of OHLC instance
    ohlc_1m.callback(ws_callback)
    doc.theme = Theme(filename=os.path.join(os.path.dirname(__file__), "theme.yaml"))


# TODO : some way to close the ohlc subscription when we dont need it anymore...


