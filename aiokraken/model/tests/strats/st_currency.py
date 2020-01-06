
from hypothesis import strategies as st

# Using partial call here to delay evaluation (and get same semantics as potentially more complex strategies)
import functools

from aiokraken.model.currency import KCurrency

KCurrencyStrategy = functools.partial(st.sampled_from, KCurrency)

if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(KCurrencyStrategy().example()))
