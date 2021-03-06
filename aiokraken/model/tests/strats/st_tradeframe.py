
from hypothesis import strategies as st

from aiokraken.model.tradeframe import TradeFrame, tradeframe
from aiokraken.rest.schemas.ktrade import KTradeModel, KTradeStrategy, TradeDictStrategy


@st.composite
def st_tradeframe(draw):
    """

    :param draw:
    :return:

    """
    trades_list = draw(st.sets(elements=KTradeStrategy(), max_size=5))  # enforcing unicity in strategy
    trades_dict = {t.trade_id: t for t in trades_list}  # building dict as it would look after marshmallow parsing

    return tradeframe(tradehistory_as_dict=trades_dict).value


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_tradeframe().example()))
