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


def bkgui(doc, ohlc_1m):  # Note : this is the bkeh app, trigger on client request...
    df = ohlc_1m.model.dataframe

    # for display
    source = ColumnDataSource(df)

    p = figure(plot_height=320, tools='pan, xwheel_zoom', toolbar_location="left",
               x_axis_type="datetime", y_axis_location="right",
               sizing_mode="scale_width")
    # extra instructions to follow the end of the x range
    # p.x_range.follow = "end"
    # p.x_range.follow_interval = pd.Timedelta(minutes=720)
    # p.x_range.range_padding = pd.Timedelta(minutes=1)

    # use a ColumnDataSource to get the stream method (on top of existing panda dataframe)
    up_source = ColumnDataSource(df[df.open < df.close])
    down_source = ColumnDataSource(df[df.close < df.open])
    # print(source)

    # set_trace()

    # draw the same plot as before
    p.segment(x0='datetime', y0='low', x1='datetime', y1='high', line_width=1, color='black', source=source)

    # inc = df.open < df.close
    # dec = df.close < df.open
    w = df.index[1] - df.index[0]  # width is one index step

    p.vbar(x='datetime', width=w, bottom='open', top='close', fill_color="#D5E1DD", line_color="black", source=up_source)
    p.vbar(x='datetime', width=w, top='open', bottom='close', fill_color="#F2583E", line_color="black", source=down_source)

    # TODO : re-add when vwap == 0 has been fixed
    # p.line(x='datetime', y='vwap', line_width=2, color='navy', source=df)

    def ohlc_widget_update(source_update, up_update = None, down_update = None):
        source.stream(source_update)
        if up_update:
            up_source.stream(up_update)
        if down_update:
            down_source.stream(down_update)

    def ws_callback(update):
        #     print(update)
        dfup = update.to_tidfrow().reset_index()
        #Note: datetime must be a normal column to appear in dict serialization

        up = dfup[dfup.open < dfup.close]
        down =dfup[dfup.close < dfup.open]

        print(dfup.to_dict('series'))
        # ERROR : _pending_writes should be non-None when we have a document lock, and we should have the lock when the document changes
        # source.stream(dfup.to_dict('list'))
        # if up:
        #     up_source.stream(up.to_dict('list'))
        # if down:
        #     down_source.stream(down.to_dict('list'))
        # finally scheduling for doc addition at next tick (when document is unlocked)
        doc.add_next_tick_callback(
            functools.partial(ohlc_widget_update,
                source_update= dfup.to_dict('series'),
                up_update=up.to_dict('series') if not up.empty else None,
                down_update=down.to_dict('series') if not down.empty else None
            )
        )

    doc.add_root(row(p, sizing_mode="scale_width"))

    # finally scheduling for doc addition at next tick (when document is unlocked)
    # doc.add_next_tick_callback(functools.partial(ohlc_widget, p))

    # adding callback for this channel via decorator method of OHLC instance
    ohlc_1m.callback(ws_callback)  # Note this means *network updates* are driving the callback (not tornado !)
    doc.theme = Theme(filename=os.path.join(os.path.dirname(__file__), "theme.yaml"))


# TODO : some way to close the ohlc subscription when we dont need it anymore...


