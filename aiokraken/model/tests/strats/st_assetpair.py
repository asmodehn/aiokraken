from hypothesis import strategies as st

from aiokraken.model.assetpair import VolumeFee, AssetPair


@st.composite
def VolumeFeeStrategy(draw, ):
    return VolumeFee(draw(st.decimals(allow_nan=False, allow_infinity=False)),
                     draw(st.decimals(allow_nan=False, allow_infinity=False))
                          )


@st.composite
def AssetPairStrategy(draw):

    return AssetPair(
        altname= draw(st.text(max_size=5)),
        wsname= draw(st.text(max_size=5)),

        aclass_base = draw(st.text(max_size=5)),
        base = draw(st.text(max_size=5)),
        aclass_quote = draw(st.text(max_size=5)),
        quote = draw(st.text(max_size=5)),

        lot = draw(st.decimals(allow_nan=False, allow_infinity=False)),
        pair_decimals= draw(st.integers(max_value=255)),
        lot_decimals= draw(st.integers(max_value=255)),
        lot_multiplier= draw(st.integers(max_value=255)),

        leverage_buy=draw(st.lists(st.integers(max_value=255), max_size=5 )),
        leverage_sell= draw(st.lists(st.integers(max_value=255), max_size=5 )),

        fees = draw(st.lists(VolumeFeeStrategy(), max_size=5 )),
        fees_maker = draw(st.lists(VolumeFeeStrategy(), max_size=5 )),
        fee_volume_currency = draw(st.text(max_size=5)),

        margin_call = draw(st.integers(max_value=255)),
        margin_stop = draw(st.integers(max_value=255))

    )


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(VolumeFeeStrategy().example()))

    for n in range(1, 10):
        print(repr(AssetPairStrategy().example()))
