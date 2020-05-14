import functools

from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


class OHLCPlot:

    def __init__(self, dataframe,  doc = None, **figure_kwargs):

        self.doc = doc

        # for display
        self.bokeh_source = ColumnDataSource(dataframe)

        # A new plot is created on every call (to kee a link with the document)
        p = figure(plot_height=320, tools='pan, wheel_zoom', toolbar_location="left",
                   x_axis_type="datetime", y_axis_location="right",
                   sizing_mode="scale_width", **figure_kwargs)
        # extra instructions to follow the end of the x range
        # p.x_range.follow = "end"
        # p.x_range.follow_interval = pd.Timedelta(minutes=720)
        # p.x_range.range_padding = pd.Timedelta(minutes=1)

        # use a ColumnDataSource to get the stream method (on top of existing panda dataframe)
        self.bokeh_up = ColumnDataSource(dataframe[dataframe.open < dataframe.close])
        self.bokeh_down = ColumnDataSource(dataframe[dataframe.close < dataframe.open])
        # print(source)

        # set_trace()

        p.segment(x0='datetime', y0='low', x1='datetime', y1='high', line_width=1, color='black', source=self.bokeh_source)

        # inc = df.open < df.close
        # dec = df.close < df.open
        w = dataframe.index[1] - dataframe.index[0]  # width is one index step

        p.vbar(x='datetime', width=w, bottom='open', top='close', fill_color="#D5E1DD", line_color="black",
               source=self.bokeh_up)
        p.vbar(x='datetime', width=w, top='open', bottom='close', fill_color="#F2583E", line_color="black",
               source=self.bokeh_down)

        # TODO : re-add when vwap == 0 has been fixed
        # p.line(x='datetime', y='vwap', line_width=2, color='navy', source=df)

        self._figure = p

    def _update_on_tornado_tick(self, source_update, up_update=None, down_update=None):
        # updating source data on tornado tick.
        self.bokeh_source.stream(source_update)
        if up_update:
            self.bokeh_up.stream(up_update)
        if down_update:
            self.bokeh_down.stream(down_update)

    def __call__(self, dataframe):
        # updating  our dataframe on network message recv
        dfup = dataframe.reset_index()
        # Note: datetime must be a normal column to appear in dict serialization

        up = dfup[dfup.open < dfup.close]
        down = dfup[dfup.close < dfup.open]

        print(dfup.to_dict('series'))
        # scheduling stream update of any doc on next tornado tick
        if self.doc:
            self.doc.add_next_tick_callback(
                functools.partial(self._update_on_tornado_tick,
                                  source_update=dfup.to_dict('series'),
                                  up_update=up.to_dict('series') if not up.empty else None,
                                  down_update=down.to_dict('series') if not down.empty else None
                                  )
            )
