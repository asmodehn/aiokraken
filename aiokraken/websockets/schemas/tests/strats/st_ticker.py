import hypothesis.strategies as st
from aiokraken.websockets.schemas.ticker import TickerWS, TickerWSSchema

from aiokraken.model.ticker import MinOrder, MinTrade, DailyValue


@st.composite
def st_minorder(draw):
    return MinOrder(
        price = draw(st.decimals()),
        whole_lot_volume = draw(st.decimals()),
        lot_volume = draw(st.decimals())
    )

@st.composite
def st_mintrade(draw):
    return MinTrade(
        price=draw(st.decimals()),
        lot_volume=draw(st.decimals())
    )

@st.composite
def st_dailyvalue(draw):
    return DailyValue(
        today=draw(st.decimals()),
        last_24_hours=draw(st.decimals())
    )

@st.composite
def st_tickerws(draw):
    return TickerWS(
        ask= draw(st_minorder()),
             bid= draw(st_minorder()),
    last_trade_closed=draw(st_mintrade()),
    volume=draw(st_dailyvalue()),
    volume_weighted_average_price=draw(st_dailyvalue()),
    high=draw(st_dailyvalue()),
    number_of_trades=draw(st_dailyvalue()),
    low=draw(st_dailyvalue()),
    todays_opening=draw(st_dailyvalue()),  # the only change from Ticker !!!!
    )



@st.composite
def st_tickerwsdict(draw):
    model = draw(st_tickerws())
    schema = TickerWSSchema()
    return schema.dump(model)


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_tickerws().example()))

    for n in range(1, 10):
        print(repr(st_tickerwsdict().example()))