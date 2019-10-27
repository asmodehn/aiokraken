import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal
from hypothesis import given, strategies as st

from aiokraken.rest.schemas.kcurrency import KCurrency
from aiokraken.rest.schemas.korderdescr import KOrderDescrSchema
from aiokraken.rest.schemas.kpair import PairModel, PairField
from aiokraken.rest.schemas.ktm import TimerField
from ..krequestorder import (
    RequestOrderSchema, RequestOrderModel, KOrderTypeModel, KABTypeModel, RequestOrderStrategy,
    RequestOrderDictStrategy,
)
from ...exceptions import AIOKrakenException

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestRequestOrderModel(unittest.TestCase):

    def setUp(self) -> None:
        # TODO : hypothesis strategy
        self.model = RequestOrderModel(pair='CRYPTOPAIR', volume=42, relative_starttm=5, relative_expiretm=2)
        # partial orderdescr
        assert 'pair' in self.model._descr_data.keys()
        # some values are already accessible in model
        assert self.model.execute is False
        assert self.model.volume == 42
        assert self.model.relative_starttm == 5
        assert self.model.relative_expiretm == 2
        assert self.model.userref is None

    def test_market_partial(self):
        m = self.model.market()
        assert m._descr_data.get('ordertype') == KOrderTypeModel.market

    def test_market_sell(self):
        m = self.model.market().sell()
        assert m.descr.ordertype == KOrderTypeModel.market
        assert m.descr.abtype == KABTypeModel.sell

    def test_market_buy(self):
        m = self.model.market().buy()
        assert m.descr.ordertype == KOrderTypeModel.market
        assert m.descr.abtype == KABTypeModel.buy

    def test_limit_partial(self):
        m = self.model.limit(limit_price=42)
        assert m._descr_data.get('ordertype') == KOrderTypeModel.limit
        assert m._descr_data.get('price') == 42

    def test_limit_sell(self):
        m = self.model.limit(limit_price=42).sell(leverage=2)
        assert m.descr.ordertype == KOrderTypeModel.limit
        assert m.descr.abtype == KABTypeModel.sell
        assert m.descr.price == 42
        assert m.descr.leverage == 2

    def test_limit_buy(self):
        m = self.model.limit(limit_price=42).buy(leverage=2)
        assert m.descr.ordertype == KOrderTypeModel.limit
        assert m.descr.abtype == KABTypeModel.buy
        assert m.descr.price == 42
        assert m.descr.leverage == 2

    def test_stop_loss_partial(self):
        m = self.model.stop_loss(stop_loss_price=51)
        assert m._descr_data.get('ordertype') == KOrderTypeModel.stop_loss
        assert m._descr_data.get('price') == 51

    def test_stop_loss_sell(self):
        m = self.model.stop_loss(stop_loss_price=51).sell(leverage=3)
        assert m.descr.ordertype == KOrderTypeModel.stop_loss
        assert m.descr.abtype == KABTypeModel.sell
        assert m.descr.leverage == 3
        assert m.descr.price == 51

    def test_stop_loss_buy(self):
        m = self.model.stop_loss(stop_loss_price=51).buy(leverage=2)
        assert m.descr.ordertype == KOrderTypeModel.stop_loss
        assert m.descr.abtype == KABTypeModel.buy
        assert m.descr.leverage == 2
        assert m.descr.price == 51

    def test_sell_partial(self):
        m = self.model.sell(leverage=2)
        assert m._descr_data.get('abtype') == KABTypeModel.sell
        assert m._descr_data.get('leverage') == 2

    def test_buy_partial(self):
        m = self.model.buy(leverage=2)
        assert m._descr_data.get('abtype') == KABTypeModel.buy
        assert m._descr_data.get('leverage') == 2

    def test_cancel(self):
        raise NotImplementedError
        m = self.model.cancel()
        assert False  # TODO : smthg...


class TestRequestOrderSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = RequestOrderSchema()
        self.descr_schema = self.schema.fields.get('descr').nested

    @given(RequestOrderStrategy())
    def test_dump_ok(self, model):
        """ Verifying that expected data parses properly """
        serialized = self.schema.dump(model)
        expected = {
            "volume": model.volume,
            "pair": PairField().serialize('v', {'v': model.pair}),
            "descr": KOrderDescrSchema().dump(model.descr),
            "validate": True,
            "userref": model.userref
        }
        if model.relative_starttm:  #if not expired
            expected.update({"relative_starttm": TimerField().serialize('v', {'v': model.relative_starttm})})
        if model.relative_expiretm:  #if not expired
            expected.update({"relative_expiretm": TimerField().serialize('v', {'v': model.relative_expiretm})})
        # check equality on dicts with usual python types, but display strings.
        assert serialized == expected, print(str(serialized) + '\n' + str(expected))

    @given(RequestOrderDictStrategy())
    def test_load_ok(self, model):
        ro = self.schema.load(model)
        assert isinstance(ro, RequestOrderModel)

    def test_load_fail(self):
        # corrupted data:
        wrg_orderstr = '{}'
        # checking it actually fails
        with self.assertRaises(Exception) as e:
            self.schema.load(wrg_orderstr)

