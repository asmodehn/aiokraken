
from aiokraken.model.tests.strats.st_asset import AssetStrategy
from aiokraken.rest.assets import Assets

import hypothesis.strategies as st


@st.composite
def st_assets(draw):
    apl = draw(st.lists(elements=AssetStrategy(), max_size=5, unique_by=lambda x: x.restname))
    return Assets(assets_as_dict={ap.restname: ap for ap in apl})


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_assets().example()))

