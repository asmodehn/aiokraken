import functools

import pandas as pd

from aiokraken.model.asset import AssetClass, Asset
from hypothesis import strategies as st


# Using partial call here to delay evaluation (and get same semantics as potentially more complex strategies)
AssetClassStrategy = functools.partial(st.sampled_from, AssetClass)


@st.composite
def AssetStrategy(draw):

    return Asset(
        altname= draw(st.text(max_size=5)),
        aclass = draw(st.text(max_size=5)),
        decimals= draw(st.integers()),
        display_decimals= draw(st.integers())
    )


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(AssetClassStrategy().example()))

    for n in range(1, 10):
        print(repr(AssetStrategy().example()))
