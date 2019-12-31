import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from aiokraken.rest.schemas.kasset import KAsset
from aiokraken.rest.schemas.kassetpair import (
    KAssetPair, KAssetPairStrategy, KDictStrategy,
    KAssetPairSchema,
)
from ..kabtype import KABTypeModel, KABTypeField, KABTypeStrategy, KABTypeStringStrategy
from ...exceptions import AIOKrakenException
from hypothesis import given, settings, Verbosity

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestKAssetPair(unittest.TestCase):

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
    @given(KAssetPairStrategy())
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


class TestKAssetPairSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = KAssetPairSchema()

    # @settings(verbosity=Verbosity.verbose)
    @given(
        KDictStrategy( KAssetPairStrategy()))
    def test_deserialize(self, modeldict):
        a = self.schema.load(modeldict)
        assert isinstance(a, KAssetPair)

    # @settings(verbosity=Verbosity.verbose)
    @given(KAssetPairStrategy())
    def test_serialize(self, model):
        a = self.schema.dump(model)

        assert 'altname' in a
        assert 'wsname' in a
        assert 'aclass_base' in a
        assert 'base' in a
        assert 'aclass_quote' in a
        assert 'quote' in a
        assert 'lot' in a
        assert 'pair_decimals' in a
        assert 'lot_decimals' in a
        assert 'lot_multiplier' in a
        assert 'leverage_buy' in a
        assert 'leverage_sell' in a
        assert 'fees' in a
        assert 'fees_maker' in a
        assert 'fee_volume_currency' in a
        assert 'margin_call' in a
        assert 'margin_stop' in a
