
from aiokraken.model.tests.strats.st_assetpair import AssetPairStrategy
from aiokraken.rest.assetpairs import AssetPairs

import hypothesis.strategies as st


@st.composite
def st_assetpairs(draw):
    # drawing asset pairs, while guarenteeing unicity of restname and wsname
    apl = draw(st.lists(elements=AssetPairStrategy(), max_size=5, unique_by=(lambda x: x.restname, lambda x: x.wsname)))
    # picking restname or wsname for key of dictionnary
    att = draw(st.sampled_from(["restname", "wsname"]))
    return AssetPairs(assetpairs_as_dict={getattr(ap, att): ap for ap in apl})


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_assetpairs().example()))

