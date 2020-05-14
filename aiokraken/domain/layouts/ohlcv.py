from typing import Dict

import bokeh.layouts
import pandas as pd

# TODO : timeframe radio buttons...
from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken.domain.models.ohlc import OHLC


class OHLCVLayout:

    def __init__(self, ohlc_tf: Dict[KTimeFrameModel, OHLC], doc=None):
        # TODO : buttons to switch between timeframes...

        from bokeh.models import RadioButtonGroup

        # tfl = [KTimeFrameModel.one_day, KTimeFrameModel.one_hour, KTimeFrameModel.one_minute]

        # radio_button_group = RadioButtonGroup(
        #     # TMP : only three main TF for now...
        #     labels=[tf.name for tf in tfl], active=0)

        # Note This will trigger data retrieval.
        plts = [d.plot(doc=doc) for d in ohlc_tf.values()]

        # callback = CustomJS(args=dict(dayref=plts[0],
        #                               hourref=plts[1],
        #                               minuteref=plts[2]), code="""
        #             var dayref_ok = dayref;
        #             var hourref_ok = hourref;
        #             var minuteref_ok = minuteref;
        #         """)
        #
        # radio_button_group.js_on_change('value', callback)

        self._layout = bokeh.layouts.column(  # radio_button_group, BUGGY TODO: FIXIT
            bokeh.layouts.row(
                *plts
            ))

    def __call__(self, dataframe):
        pass  # To manage updates...


