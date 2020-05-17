"""
Data Driven Bokeh
"""
from __future__ import annotations

from collections import namedtuple

import pandas
import typing
from bokeh.document import Document
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Plot
from bokeh.plotting import Figure
from bokeh.util.serialization import convert_datetime_array, convert_datetime_type
from bokeh.document import without_document_lock

# represents the relationship of a source used by a doc.
DDLink = namedtuple("DDLink", ["source", "doc"])


class DDModel:  # rename to source TODO

    _data: pandas.DataFrame
    _process: typing.List[typing.Callable]

    _links: typing.Set[DDLink]  # TODO that link is likely hidden in the plot somewhere...
    _rendered_datasources: typing.List[ColumnDataSource] #TODO : replace links with this... document is a property of datasource

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, new_data):

        if True: # Debug HACK
            # The quick and simple way
            self._data = new_data
            for rds in self._rendered_datasources:
                rds.document.add_next_tick_callback(
                    lambda: setattr(rds, 'data', new_data)
                )
            return

        # The long and winding road...

        appended_index = new_data.index.difference(self._data.index)
        patched_index = new_data.index.intersection(self._data.index)

        available_patches = new_data.loc[patched_index]

        # if we have some potential patches
        if available_patches.any(axis='columns').any():
            # only patch data differences
            patchfilter = available_patches.isin(self._data)
            patchable = available_patches.loc[(~patchfilter.all(axis='columns')).index]

            if self._debug:
                print(f"Patch update: \n{patchable}")

            if patchable.any(axis='columns').any():
                # to avoid bug where series are iterated as list without index
                # TypeError: cannot unpack non-iterable int object
                patches = dict()
                for col, pseries in patchable.to_dict('series').items():
                    # we need to convert timestamp index to int (!?!?) in the patch before sending...
                    patches[col] = [(int(convert_datetime_type(i)), v) for i, v in pseries.iteritems()]
                for l in self._links:
                    # l.doc.add_next_tick_callback(
                        # full upate of previously instantiated sources
                        # lambda: l.source.patch(patches) #TODO : review this : explicit pathc needed or not ??
                        # TODO : FIX : ValueError: Out-of bounds index (1589734548783) in patch for column: random1

                        # lambda: setattr(l.source, 'data', new_data)
                        # TODO : FIX RuntimeError: _pending_writes should be non-None when we have a document lock, and we should have the lock when the document changes
                    # )
                    pass

        streamable = new_data.loc[appended_index]

        if self._debug:
            print(f"Stream update: \n{streamable}")

        if streamable.any(axis='columns').any():
            # streamable = streamable.reset_index().to_dict('series')
            # to prevent ValueError: Must stream updates to all existing columns (missing: level_0)
            # streamable['index'] = convert_datetime_array(streamable['index'].to_numpy())
            # to prevent error on timestamp
            for l in self._links:
                l.doc.add_next_tick_callback(
                    lambda: l.source.stream(streamable),  # stream delta values first
                )

        self._data = new_data

    """ class representing one viewplot - potentially rendered in multiple documents """
    def __init__(self, data: pandas.DataFrame, debug=True):
        self._debug = debug
        self._data = data
        self._links = set()
        self._rendered_datasources = list()
        # a set here is fine, it is never included in the bokeh document

    def __call__(self, doc: Document):
        # we need to rest the index just before rendering to bokeh
        # it is useful for stream and patches computation
        src = ColumnDataSource(data=self._data)

        self._rendered_datasources.append(src)

        self._links.add(DDLink(doc=doc, source=src))
        # TODO : how to prune this set ?
        return src  # return datasource for use by the view


class DDLine:  # TODO : make more of these

    _source: DDModel

    # shortcut to data
    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, new_source):
        self._source = new_source

    def __init__(self, source: DDModel, x, y, **line_kwargs):

        assert x in (['index'] + source.data.columns.to_list())
        assert y in (['index'] + source.data.columns.to_list())

        self._source = source

        self.plot_kwargs = line_kwargs

    def __call__(self, doc: Document, fig: Figure):
        bkh_source = self._source(doc=doc)
        fig.line(**self.plot_kwargs, source=bkh_source)


class DDFigure:  #  TODO: inherit from DDModel as well ??
    # TODO Maybe after we can manage a dataframe cleanly :
    #  categorical product of dataframe is a categorical product of plots...
    #  Wether a new figure is needed is determined by column type (and unit compatibility - see pint)
    """
    A class used as interface to bokeh Figure class.
    """

    # TODO : support complex operations on the dataframe
    #  to implement visual feedback on compute...

    def __init__(self,  **figure_kwargs):

        self._figure_kwargs = figure_kwargs

        self._ddplots = dict()

    def view(self, doc: Document):  # TODO : in a __call__
        # delegate to bokeh only when needed (figure cannot be in multiple docs)
        fig = Figure(**self._figure_kwargs)

        # do all the necessary plotting and save the datasources
        for n, plot in self._ddplots.items():
            plot(doc=doc, fig=fig)

        return fig

    def __getitem__(self, item) -> DDModel:
        return self._ddplots[item]

    def __setitem__(self, key, value: DDModel):
        self._ddplots[key] = value

    def line(self, source: DDModel, plotname: str, legend: bool = True, **extrakwargs):

        plot = DDLine(source=source,
                      name=plotname,
                    legend_label= plotname if legend else None,
                    x = "index",
                    **extrakwargs)

        self._ddplots[plotname]= plot
        return plot


if __name__ == '__main__':
    # Minimal server test
    import random
    import asyncio
    from datetime import datetime, timedelta

    from bokeh.server.server import Server as BokehServer

    # Note : This is "created" before a document output is known
    # and before a request is sent to the server
    start = datetime.now()
    ddsource1 = DDModel(pandas.DataFrame(data=[random.randint(-10, 10), random.randint(-10, 10)], columns=["random1"],
                                         index=[start, start+timedelta(milliseconds=1)]))
    ddsource2 = DDModel(pandas.DataFrame(data=[random.randint(-10, 10), random.randint(-10, 10)], columns=["random2"],
                                         index=[start, start+timedelta(milliseconds=1)]))
    # Note we add some initial data to have bokeh center the plot properly on hte time axis TODO : fix it !

    # views are setup in advance as well

    # Note : This is "created" before a document output is known and before a request is sent to the server
    view = DDFigure(title="Random Test", plot_height=480,
                    tools='xpan, xwheel_zoom, reset',
                    toolbar_location="left", y_axis_location="right",
                    x_axis_type='datetime', sizing_mode="scale_width")

    plot1 = view.line(source=ddsource1, plotname="Random1", y="random1", color="blue")
    plot2 = view.line(source=ddsource2, plotname="Random2", y="random2", color="red")

    # Producer as a background task
    async def compute_random(m, M):
        tick = list()  # to help with full data generation
        while True:
            now = datetime.now()
            tick.append(now)
            print(now)  # print in console for explicitness

            # push FULL data updates !
            # Note some derivative computation may require more than you think
            plot1.source.data = pandas.DataFrame(
                columns=["random1"],
                data = {
                    "random1": [
                    random.randint(m, M)
                    for t in range(len(tick))
                ]},
                index = tick
            )

            # add extra data points will NOT trigger dynamic updates
            plot2.source.data.loc[now] = random.randint(m, M)

            await asyncio.sleep(1)

    def test_page(doc):
        # Debug Figure
        debug_fig = Figure(**view._figure_kwargs)
        # simple bokeh style
        source1 = ColumnDataSource(ddsource1.data)
        source2 = ColumnDataSource(ddsource2.data)
        # dynamic datasource as simply as possible
        p1 = debug_fig.line(x="index", y="random1", color="blue", source=source1)
        p2 = debug_fig.line(x="index", y="random2", color="red", source=source2)

        dynfig = view.view(doc=doc)
        doc.add_root(
            column(
                dynfig,
                # to help compare / visually debug
                debug_fig
            )
        )
        # doc.theme = Theme(filename=os.path.join(os.path.dirname(__file__), "theme.yaml"))

        # quick and easy dynamic update
        doc.add_periodic_callback(
            lambda: (
                # replacing data in datasource directly trigger simple dynamic update in plots.
                setattr(source1,'data', ddsource1.data),
                setattr(source2,'data', ddsource2.data)
            ),
            period_milliseconds=1000
        )

    def start_tornado(bkapp):
        # Server will take current running asyncio loop as his own.
        server = BokehServer({'/': bkapp})  # iolopp must remain to none, num_procs must be default (1)
        server.start()
        return server

    async def main():

        print(f"Starting Tornado Server...")
        server = start_tornado(bkapp=test_page)
        # Note : the bkapp is run for each request to the url...

        # bg task...
        asyncio.create_task(compute_random(-10, 10))

        print('Serving Bokeh application on http://localhost:5006/')
        # server.io_loop.add_callback(server.show, "/")

        # THIS is already the loop that is currently running !!!
        assert server.io_loop.asyncio_loop == asyncio.get_running_loop(), f"{server.io_loop.asyncio_loop} != {asyncio.get_running_loop()}"
        # server.io_loop.start()  # DONT NEED !

        await asyncio.sleep(3600)  # running for one hour.
        # TODO : scheduling restart (crontab ? cli params ?) -> GOAL: ensure resilience (erlang-style)

    asyncio.run(main())







