import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from aiokraken.model.tests.strats.st_assetpair import AssetPair, AssetPairStrategy
from aiokraken.rest.schemas.kassetpair import ( KDictStrategy,
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

class TestKAssetPairSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = KAssetPairSchema()

    # @settings(verbosity=Verbosity.verbose)
    @given(
        KDictStrategy(AssetPairStrategy()))
    def test_deserialize(self, modeldict):
        a = self.schema.load(modeldict)
        assert isinstance(a, AssetPair)

    # @settings(verbosity=Verbosity.verbose)
    @given(AssetPairStrategy())
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
