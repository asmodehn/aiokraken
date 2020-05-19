import typing

import bokeh
import pandas
from bokeh.layouts import column, row
from bokeh.palettes import viridis

from aiokraken.domain.models.figures.ddbokeh import DDSharedDataSource
from bokeh.models import ColumnDataSource, DataTable, DateFormatter, Model, TableColumn
from bokeh.plotting import Figure


class BokehLiveView:

    figure: Figure

    def __init__(self, source: DDSharedDataSource, **figure_kwargs):
        self.figure = Figure(**figure_kwargs)

        palette = viridis(len(source.data.columns))
        color_index = {c: palette[i] for i, c in enumerate(source.data.columns)}

        for c in source.data.columns:
            # TODO : maybe only pass the necessary column ?
            self.figure.line(source=source(), x="index", y=c, color=color_index[c],)

    def __getitem__(self, item):
        return self.figure.renderers[item]


    #
    #
    # def __call__(self, doc):
    #     """ to display the view in a bokeh document """
    #     # We do all the usual bokeh calls here...
    #
    #     # create figure from args
    #
    #     #for each plot actually create renderers (they manage their own source)
    #     for p in self.plots:
    #         p(fig=fig)
    #
    #     # return the figure (as rendering of the view)
    #     return fig




if __name__ == '__main__':
    # Minimal server test
    import random
    import asyncio
    from datetime import datetime, timedelta

    from bokeh.server.server import Server as BokehServer

    # Note : This is "created" before a document output is known
    # and before a request is sent to the server
    start = datetime.now()
    ddsource1 = DDSharedDataSource(name="ddsource1", data=pandas.DataFrame(data=[
            [random.randint(-10, 10), random.randint(-10, 10)],
            [random.randint(-10, 10), random.randint(-10, 10)],
        ],
            columns=["random1", "random2"],
            index=[start, start+timedelta(milliseconds=1)]
    ))

    # Note : This is "created" before a document output is known and before a request is sent to the server
    view = BokehLiveView(source=ddsource1, title="Random Test", plot_height=480,
                    tools='xpan, xwheel_zoom, reset',
                    toolbar_location="left", y_axis_location="right",
                    x_axis_type='datetime', sizing_mode="scale_width")

    # Producer as a background task
    async def compute_random(m, M):
        tick = ddsource1.data.index.to_list()  # to help with full data generation
        while True:
            now = datetime.now()
            tick.append(now)
            print(now)  # print in console for explicitness

            new_data = {
                    "random1": [
                        random.randint(m, M)  # change everything to trigger patch
                        for t in range(len(tick))  # + 1 extra element to stream
                    ],
                    "random2": ddsource1.data["random2"].to_list() + [
                        random.randint(m, M)  # only add one element to stream
                    ]
                }

            # push FULL data updates !
            # Note some derivative computation may require more than you think
            ddsource1.data = pandas.DataFrame(
                columns=["random1", "random2"],
                data = new_data,
                index = tick
            )

            await asyncio.sleep(1)

    def test_page(doc):

        doc.add_root(
            column(
                row(view.figure, ddsource1.table),
            )
        )
        # doc.theme = Theme(filename=os.path.join(os.path.dirname(__file__), "theme.yaml"))

        # quick and easy dynamic update
        # doc.add_periodic_callback(
        #     lambda: (
        #         # replacing data in datasource directly trigger simple dynamic update in plots.
        #         setattr(d1.data_source, 'data', ddsource1.data),
        #         setattr(d2.data_source, 'data', ddsource2.data),
        #
        #         setattr(debugdt.source, 'data', ddsource1.data),
        #         setattr(debugdt.source, 'data', ddsource2.data),
        #         # setattr(plot1.source, 'data', ddsource1.data),
        #         # setattr(plot2.source, 'data', ddsource2.data),
        #     ),
        #     period_milliseconds=1000
        # )

    def start_tornado(bkapp):
        # Server will take current running asyncio loop as his own.
        server = BokehServer({'/': bkapp})  # iolopp must remain to none, num_procs must be default (1)
        server.start()
        return server

    async def main():

        print(f"Starting Tornado Server...")
        server = start_tornado(bkapp=test_page)
        # Note : the bkapp is run for each request to the url...

        # bg async task...TMP deactivate, DEBUG problem on first render
        asyncio.create_task(compute_random(-10, 10))

        print('Serving Bokeh application on http://localhost:5006/')
        # server.io_loop.add_callback(server.show, "/")

        # THIS is already the loop that is currently running !!!
        assert server.io_loop.asyncio_loop == asyncio.get_running_loop(), f"{server.io_loop.asyncio_loop} != {asyncio.get_running_loop()}"
        # server.io_loop.start()  # DONT NEED !

        await asyncio.sleep(3600)  # running for one hour.
        # TODO : scheduling restart (crontab ? cli params ?) -> GOAL: ensure resilience (erlang-style)

    asyncio.run(main())



