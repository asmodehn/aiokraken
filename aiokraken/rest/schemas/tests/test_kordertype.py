import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from ..kordertype import KOrderTypeModel, KOrderTypeField
from ...exceptions import AIOKrakenException

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestOrderTypeModel(unittest.TestCase):

    def test_unknown(self):
        with self.assertRaises(ValueError):
            KOrderTypeModel('unknown')

    def test_market(self):
        # TODO : hypothesis strategy
        self.model = KOrderTypeModel('market')
        assert self.model == KOrderTypeModel.market

    def test_limit(self):
        # TODO : hypothesis strategy
        self.model = KOrderTypeModel('limit')
        assert self.model == KOrderTypeModel.limit

    def test_stop_loss(self):
        # TODO : hypothesis strategy
        self.model = KOrderTypeModel('stop-loss')
        assert self.model == KOrderTypeModel.stop_loss

    def test_take_profit(self):
        # TODO : hypothesis strategy
        self.model = KOrderTypeModel('take-profit')
        assert self.model == KOrderTypeModel.take_profit


class TestOrderTypeField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = KOrderTypeField()

    @parameterized.expand([
        # we make sure we are using a proper json string
        ['market', KOrderTypeModel.market],
        ['limit', KOrderTypeModel.limit],
        ['stop-loss', KOrderTypeModel.stop_loss],
        ['take-profit', KOrderTypeModel.take_profit]
    ])
    def test_deserialize(self, ordertypestr, expectedmodel):
        p = self.field.deserialize(ordertypestr)
        assert isinstance(p, KOrderTypeModel)
        assert p is expectedmodel

    @parameterized.expand([
        # we make sure we are using a proper json string
        [KOrderTypeModel.market, 'market'],
        [KOrderTypeModel.limit, 'limit'],
        [KOrderTypeModel.stop_loss, 'stop-loss'],
        [KOrderTypeModel.take_profit, 'take-profit']
    ])
    def test_serialize(self, ordertypemodel, expectedstr):
        ot = self.field.serialize('ordertype', {'ordertype': ordertypemodel})
        assert ot == expectedstr, ot
