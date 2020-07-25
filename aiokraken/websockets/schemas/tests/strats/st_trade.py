import hypothesis.strategies as st
from aiokraken.websockets.schemas.trade import TradeWS, TradeWSSchema

from aiokraken.websockets.schemas.ticker import TickerWS, TickerWSSchema, MinOrder, MinTrade, DailyValue


@st.composite
def st_tradews(draw):
    return TradeWS(
        price= draw(st.floats(allow_nan=False, allow_infinity=False)),
        volume= draw(st.floats(allow_nan=False, allow_infinity=False)),
        time= draw(st.floats(allow_nan=False, allow_infinity=False)),
        side= draw(st.text()),
        orderType = draw(st.text()),
        misc= draw(st.text()),
    )


@st.composite
def st_tradewsdict(draw):
    model = draw(st_tradews())
    schema = TradeWSSchema()
    return schema.dump(model)


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_tradews().example()))

    for n in range(1, 10):
        print(repr(st_tradewsdict().example()))
