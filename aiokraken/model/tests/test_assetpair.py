import decimal
import unittest

from hypothesis import given

from aiokraken.model.tests.strats.st_assetpair import AssetPairStrategy

class TestAssetPair(unittest.TestCase):

# <pair_name> = pair name
#     altname = alternate pair name
#     wsname = WebSocket pair name (if available)
#     aclass_base = asset class of base component
#     base = asset id of base component
#     aclass_quote = asset class of quote component
#     quote = asset id of quote component
#     lot = volume lot size
#     pair_decimals = scaling decimal places for pair
#     lot_decimals = scaling decimal places for volume
#     lot_multiplier = amount to multiply lot volume by to get currency volume
#     leverage_buy = array of leverage amounts available when buying
#     leverage_sell = array of leverage amounts available when selling
#     fees = fee schedule array in [volume, percent fee] tuples
#     fees_maker = maker fee schedule array in [volume, percent fee] tuples (if on maker/taker)
#     fee_volume_currency = volume discount currency
#     margin_call = margin call level
#     margin_stop = stop-out/liquidation margin level


    # @settings(verbosity=Verbosity.verbose)
    @given(AssetPairStrategy())
    def test_model(self, model):
        assert isinstance(model.altname, str)
        assert isinstance(model.wsname, str)
        assert isinstance(model.aclass_base, str)
        assert isinstance(model.base, str)
        assert isinstance(model.aclass_quote, str)
        assert isinstance(model.quote, str)
        assert isinstance(model.lot, decimal.Decimal)
        assert isinstance(model.pair_decimals, int)
        assert isinstance(model.lot_decimals, int)
        assert isinstance(model.lot_multiplier, int)
        assert isinstance(model.leverage_buy, list)
        assert isinstance(model.leverage_sell, list)
        assert isinstance(model.fees, list)  #KFees)
        assert isinstance(model.fees_maker, list )  #KFees)
        assert isinstance(model.fee_volume_currency, str)  #KFeeCurrency)
        assert isinstance(model.margin_call, int)
        assert isinstance(model.margin_stop, int)



if __name__ == "__main__":
    unittest.main()