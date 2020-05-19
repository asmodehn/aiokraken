"""
Data Driven Bokeh
"""
from __future__ import annotations

from collections import namedtuple

import pandas
import typing
from bokeh.document import Document
from bokeh.layouts import column, row
from bokeh.plotting import Figure
from bokeh.models import ColumnDataSource, GlyphRenderer, Plot, DataTable, TableColumn, DateFormatter
from bokeh.util.serialization import convert_datetime_array, convert_datetime_type
from bokeh.document import without_document_lock

# represents the relationship of a source used by a doc.
DDLink = namedtuple("DDLink", ["source", "doc"])


class DDSharedDataSource:

    _data: pandas.DataFrame
    _process: typing.List[typing.Callable]

    _rendered_datasources: typing.List[ColumnDataSource]
    # REMINDER : document is a property of bokeh's datasource

    def _stream(self, streamable):
        try:
            if streamable.any(axis='columns').any():
                # TODO: log stream detected properly
                print(f"Stream update: \n{streamable}")

                # streamable = streamable.reset_index().to_dict('series')
                # to prevent ValueError: Must stream updates to all existing columns (missing: level_0)
                # streamable['index'] = convert_datetime_array(streamable['index'].to_numpy())
                # to prevent error on timestamp
                for r in self._rendered_datasources:  # TODO : link is gone, document is inside the rendered source...
                    if r.document is not None:
                        r.document.add_next_tick_callback(
                            lambda: r.stream(streamable),  # stream delta values first
                        )

        except Exception as e:
            print(e)  # log it and keep going, the data will be replace in datasource anyway.

    def _patch(self, patchable):

        try:
            if patchable.any(axis='columns').any():
                # TODO: log patch detected properly
                print(f"Patch update: \n{patchable}")

                # to avoid bug where series are iterated as list without index
                # TypeError: cannot unpack non-iterable int object
                patches = dict()
                # Note : seems we need the integer index for patch, not the timestamp integer...
                for col, pseries in patchable.reset_index(drop=True).items():
                    patches[col] = [t for t in pseries.items()]
                for r in self._rendered_datasources:
                    if r.document is not None:
                        r.document.add_next_tick_callback(
                            # full upate of previously instantiated sources
                            lambda: r.patch(patches)
                        )
        except Exception as e:
            print(e)  # log it and keep going, the data will be replace in datasource anyway.

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, new_data):

        assert new_data.index.is_unique  # To be sure we keep unique index... (Set semantics for simplicity)

        # Attempting to discover appends and patches based on index...
        data_index = self._data.index
        appended_index = new_data.index.difference(data_index)
        patched_index = new_data.index.intersection(data_index)

        available_patches = new_data.loc[patched_index]

        # if we have some potential patches
        if available_patches.any(axis='columns').any():
            # only patch data differences
            patchfilter = available_patches.isin(self._data)
            patchable_indices = (~patchfilter.all(axis='columns')).index
            patchable = available_patches.loc[patchable_indices]

            self._patch(patchable)

        streamable = new_data.loc[appended_index]

        self._stream(streamable)

        # Replace data here and in existing datasources.
        # This will trigger update of simple view, like datatable.
        # BUT it will NOT trigger redraw of the various plots, we rely on stream or patch for that.
        self._data = new_data
        for rds in self._rendered_datasources:
            if rds.document is not None:
                rds.document.add_next_tick_callback(
                    lambda: setattr(rds, 'data', new_data)
                )

    @property
    def table(self):
        """ Simplest model to visually help debug interactive update.
            This does NOT require us to call stream or patch.
        """
        # Note : Since the Datatable is managed by bokeh directly for dynamic updates,
        # we do not need to register our datasource in this case
        ds = ColumnDataSource(data=self._data, name=f"{self._name}_tableview")

        # TODO: BUG ? somehow adding datatable's data source prevent patches to happen propery on plot ??
        # self._rendered_datasources.append(ds)

        dt = DataTable(source=ds, columns=[
                                              TableColumn(field="index", title="index",
                                                          formatter=DateFormatter(format="%m/%d/%Y %H:%M:%S"))] + [
                                              TableColumn(field=n, title=n) for n in self.data.columns if
                                              n != "index"
                                          ],
              width=320, height=480)
        return dt

    def line(self, fig, y="random1", color="blue", legend_label="lineview"):
        # Debug renderer
        return fig.line(x="index", y=y, color=color, source=self(name=f"{self._name}_as_{legend_label}"), legend_label=legend_label)

    # TODO: multilines... various figures visualization + customization...
    # def plot(self, palette=None):
    #     fig = Figure(title="Random Test", plot_height=480,
    #            tools='pan, xwheel_zoom, reset',
    #            toolbar_location="left", y_axis_location="right",
    #            x_axis_type='datetime', sizing_mode="scale_width")
    #
    #     palette = Spectral11[0:numlines] if palette is None else palette
    #
    #     fig.multi_line(x="index", y=c, color=, source = self(name=f"{self._name}[{c}]"), legend_label=c)

    """ class representing one viewplot - potentially rendered in multiple documents """
    def __init__(self, data: pandas.DataFrame, name:str, debug=True):
        self._debug = debug
        self._name = name
        self._data = data
        self._links = set()
        self._rendered_datasources = list()
        # a set here is fine, it is never included in the bokeh document

    def __call__(self, name=None) -> ColumnDataSource:
        # we need to rest the index just before rendering to bokeh
        # it is useful for stream and patches computation
        src = ColumnDataSource(data=self._data, name=self._name if name is None else name)  # Note: name is mostly for debugging help

        self._rendered_datasources.append(src)
        # TODO : how to prune this list ? shall we ever ?
        # note that _detach_document seems to be called properly by bokeh and datasource's document is set to None.

        return src  # return datasource for use by the view


if __name__ == '__main__':
    # Minimal server test
    import random
    import asyncio
    from datetime import datetime, timedelta

    from bokeh.server.server import Server as BokehServer

    # Note : This is "created" before a document output is known
    # and before a request is sent to the server
    start = datetime.now()
    ddsource1 = DDSharedDataSource(name="ddsource1", data=pandas.DataFrame(data=[random.randint(-10, 10), random.randint(-10, 10)], columns=["random1"],
                                                    index=[start, start+timedelta(milliseconds=1)]))
    ddsource2 = DDSharedDataSource(name="ddsource2", data=pandas.DataFrame(data=[random.randint(-10, 10), random.randint(-10, 10)], columns=["random2"],
                                                    index=[start, start+timedelta(milliseconds=1)]))
    # Note we add some initial data to have bokeh center the plot properly on the time axis TODO : fix it !

    # Producer as a background task
    async def compute_random(m, M):
        tick = list()  # to help with full data generation
        while True:
            now = datetime.now()
            tick.append(now)
            print(now)  # print in console for explicitness

            # push FULL data updates !
            # Note some derivative computation may require more than you think
            ddsource1.data = pandas.DataFrame(
                columns=["random1"],
                data = {
                    "random1": [
                    random.randint(m, M)
                    for t in range(len(tick))
                ]},
                index = tick
            )

            # add extra data points will NOT trigger dynamic updates
            ddsource2.data.loc[now] = random.randint(m, M)

            await asyncio.sleep(1)

    def test_page(doc):
        # Debug Figure
        debug_fig = Figure(title="Random Test", plot_height=480,
                        tools='pan, xwheel_zoom, reset',
                        toolbar_location="left", y_axis_location="right",
                        x_axis_type='datetime', sizing_mode="scale_width")

        # dynamic datasource plots as simply as possible
        ddsource1.line(fig=debug_fig, y="random1", color="blue", legend_label="Debug1")
        # plot1 = debug_fig.line(x="index", y="random1", color="blue", source=ds1, legend_label="Debug1")
        plot2 = debug_fig.line(x="index", y="random2", color="red", source=ddsource2("debug_static_line2"), legend_label="Debug2")

        # import inspect
        # for d, b in zip(dir(dynfig), dir(debug_fig)):
        #     if getattr(dynfig,d) != getattr(debug_fig,b) and not inspect.ismethod(getattr(dynfig,d) ):
        #         print(f"{d} : { getattr(dynfig,d)} != {getattr(debug_fig,b)}")

        doc.add_root(
                # to help compare / visually debug
                row(debug_fig, ddsource1.table, ddsource2.table)
        )
        # doc.theme = Theme(filename=os.path.join(os.path.dirname(__file__), "theme.yaml"))

        # quick and easy dynamic update
        doc.add_periodic_callback(
            lambda: (
                # replacing data in datasource directly trigger simple dynamic update in plots.
                # setattr(ds1, 'data', ddsource1.data),
                # This is mandatory because the data update is not detected by the livedatasource
                # setattr(plot2.data_source, 'data', ddsource2.data)
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

        # bg async task...
        asyncio.create_task(compute_random(-10, 10))

        print('Serving Bokeh application on http://localhost:5006/')
        # server.io_loop.add_callback(server.show, "/")

        # THIS is already the loop that is currently running !!!
        assert server.io_loop.asyncio_loop == asyncio.get_running_loop(), f"{server.io_loop.asyncio_loop} != {asyncio.get_running_loop()}"
        # server.io_loop.start()  # DONT NEED !

        await asyncio.sleep(3600)  # running for one hour.
        # TODO : scheduling restart (crontab ? cli params ?) -> GOAL: ensure resilience (erlang-style)

    asyncio.run(main())







