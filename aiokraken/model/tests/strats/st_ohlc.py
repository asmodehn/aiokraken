from datetime import datetime, timedelta
import pandas as pd
from aiokraken.model.ohlc import OHLC
from hypothesis import strategies as st


@st.composite
def st_ohlc(draw):

    def builder(*elems):
        return list((int(elems[0].timestamp()), str(elems[1]), str(elems[2]), str(elems[3]), str(elems[4]), str(elems[5]), str(elems[6]), elems[7]))

    dfstrat = st.lists(
        elements=st.builds(
            builder,
            st.datetimes(min_value=datetime.now() - timedelta(days=365), max_value=datetime.now() + timedelta(days=365)),
            st.decimals(allow_nan=False, allow_infinity=False),
            st.decimals(allow_nan=False, allow_infinity=False),
            st.decimals(allow_nan=False, allow_infinity=False),
            st.decimals(allow_nan=False, allow_infinity=False),
            st.decimals(allow_nan=False, allow_infinity=False),
            st.decimals(allow_nan=False, allow_infinity=False),
            st.integers(min_value=0)
        ),
        min_size=1  # to get a 'last'
    )

    df = pd.DataFrame(draw(dfstrat),
                      columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
                      )
    df.set_index('time')
    sorted = df.sort_index()

    return OHLC(sorted, last=df['time'].iloc[-1])








# @parameterized.expand([
#     [pd.DataFrame(
#         # TODO:   proper Time, proper currencies...
#         [[1567039620, 8746.4, 8751.5, 8745.7, 8745.7, 8749.3, 0.09663298, 8],
#          [1567039680, 8745.7, 8747.3, 8745.7, 8747.3, 8747.3, 0.00929540, 1]],
#         # grab that from kraken documentation
#         columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
#     ), 1567041780],
# ])
# def test_load_ok(self, df, last):
#     """ Verifying that expected data parses properly """
#     ohlc = OHLC(data=df, last=last)


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_ohlc().example()))
