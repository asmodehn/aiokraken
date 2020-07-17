from aiokraken.model.asset import AssetModel
from aiokraken.model.tests.strats.st_asset import AssetStrategy
from aiokraken.rest.assets import Assets

import hypothesis.strategies as st


@st.composite
def st_assets(draw):
    d = draw(st.dictionaries(keys=st.text(min_size=3, max_size=8), values=AssetStrategy(), max_size=5))
    return Assets(assets_as_dict=d)


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_assets().example()))

