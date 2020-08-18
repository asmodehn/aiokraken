
from hypothesis import strategies as st

from aiokraken.model.pair import PairModel
from aiokraken.model.tests.strats.st_currency import KCurrencyStrategy


@st.composite
def PairStrategy(draw):
    """

    :param draw:
    :return:

    """
    base = draw(KCurrencyStrategy())
    quote= draw(KCurrencyStrategy().filter(lambda c: c != base))
    return PairModel(base=base, quote=quote)


# This makes hypothesis blow up because of inability to shrink...
# @st.composite
# def PairStrategy(draw, base=KCurrencyStrategy(), quote=KCurrencyStrategy()):
#     b = draw(base)
#     q = draw(quote)
#     while q == b:
#         q = draw(quote)
#     return PairModel(base=b, quote=q)


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(PairStrategy().example()))
