
# from bokeh.driving import count
# from bokeh.layouts import column, gridplot, row
import pandas
from bokeh.models import ColumnDataSource, Select, Slider
from bokeh.plotting import figure, show

TOOLS = "pan,wheel_zoom,box_zoom,reset,save"

# Ref : https://github.com/bokeh/bokeh/tree/2.0.0/examples/app/ohlc
# Another : https://stackoverflow.com/questions/41448431/plotting-a-candlestick-chart-with-custom-per-candlestick-individual-coloring

def fig_ohlc(df: pandas.DataFrame, **kwargs):

    p = figure(plot_height=320, tools=TOOLS, x_axis_type="datetime", y_axis_location="right", sizing_mode="scale_width",  **kwargs)
    # extra instructions to follow the end of the x range
    # p.x_range.follow = "end"
    # p.x_range.follow_interval = pd.Timedelta(minutes=720)
    # p.x_range.range_padding = pd.Timedelta(minutes=1)

    # use a ColumnDataSource to get the stream method (on top of existing panda dataframe)
    source = ColumnDataSource(df)
    # print(source)

    # set_trace()

    # draw the same plot as before
    p.segment(x0='datetime', y0='low', x1='datetime', y1='high', line_width=1, color='black', source=df)

    inc = df.open < df.close
    dec = df.close < df.open
    w = df.index[1] - df.index[0]  # width is one index step

    p.vbar(x=df.index[inc], width=w, bottom=df.open[inc], top=df.close[inc], fill_color="#D5E1DD", line_color="black")
    p.vbar(x=df.index[dec], width=w, top=df.open[dec], bottom=df.close[dec], fill_color="#F2583E", line_color="black")

    # TODO : re-add when vwap == 0 has been fixed
    # p.line(x='datetime', y='vwap', line_width=2, color='navy', source=df)

    return p
