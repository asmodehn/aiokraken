from aiokraken.model.asset import AssetModel
from aiokraken.model.tests.strats.st_assetpair import AssetPairStrategy
from aiokraken.rest.assetpairs import AssetPairs

import hypothesis.strategies as st


@st.composite
def st_assetpairs(draw):
    d = draw(st.dictionaries(keys=st.text(min_size=3, max_size=8), values=AssetPairStrategy(), max_size=5))
    return AssetPairs(assetpairs_as_dict=d)


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_assetpairs().example()))

