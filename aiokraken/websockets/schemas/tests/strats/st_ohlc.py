import hypothesis.strategies as st

from aiokraken.websockets.schemas.ohlc import OHLCUpdate, OHLCUpdateSchema


@st.composite
def st_ohlcupdate(draw):
    return OHLCUpdate(
        time= draw(st.floats(allow_nan=False, allow_infinity=False)),
        etime= draw(st.floats(allow_nan=False, allow_infinity=False)),
        open= draw(st.floats(allow_nan=False, allow_infinity=False)),
        high= draw(st.floats(allow_nan=False, allow_infinity=False)),
        low= draw(st.floats(allow_nan=False, allow_infinity=False)),
        close= draw(st.floats(allow_nan=False, allow_infinity=False)),
        vwap= draw(st.floats(allow_nan=False, allow_infinity=False)),
        volume= draw(st.floats(allow_nan=False, allow_infinity=False)),
        count= draw(st.integers())
    )


@st.composite
def st_ohlcupdatedict(draw):
    model = draw(st_ohlcupdate())
    schema = OHLCUpdateSchema()
    return schema.dump(model)


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_ohlcupdate().example()))

    for n in range(1, 10):
        print(repr(st_ohlcupdatedict().example()))
