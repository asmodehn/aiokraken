import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal
from hypothesis import given, strategies as st

from aiokraken.rest.schemas.kcurrency import KCurrency
from aiokraken.rest.schemas.kabtype import KABTypeModel
from aiokraken.rest.schemas.kordertype import KOrderTypeModel
from aiokraken.rest.schemas.korderdescr import KOrderDescrSchema
from aiokraken.rest.schemas.kpair import PairModel, PairField
from aiokraken.rest.schemas.ktm import TimerField
from ..krequestorder import (
    RequestOrder,
    RequestOrderNoPriceStrategy,
    RequestOrderOnePriceStrategy,
    RequestOrderTwoPriceStrategy,

    RequestOrderNoPrice,
    RequestOrderNoPriceFinalized,
    RequestOrderFinalizeStrategy,
    RequestOrderTwoPrice,
    RequestOrderTwoPriceFinalized,
    RequestOrderOnePriceFinalized,
    RequestOrderOnePrice,
)
from ...exceptions import AIOKrakenException

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestRequestOrder(unittest.TestCase):

    @given(st.builds(RequestOrder))
    def test_model(self, model):
        assert isinstance(model, RequestOrder)
        assert hasattr(model, "pair") and isinstance(model.pair, PairModel)

        assert hasattr(model, "market") and callable(model.market)
        assert hasattr(model, "limit") and callable(model.limit)
        assert hasattr(model, "stop_loss") and callable(model.stop_loss)
        assert hasattr(model, "take_profit") and callable(model.take_profit)
        assert hasattr(model, "stop_loss_profit") and callable(model.stop_loss_profit)
        assert hasattr(model, "stop_loss_profit_limit") and callable(
            model.stop_loss_profit_limit
        )
        assert hasattr(model, "stop_loss_limit") and callable(model.stop_loss_limit)
        assert hasattr(model, "take_profit_limit") and callable(model.take_profit_limit)
        assert hasattr(model, "trailing_stop") and callable(model.trailing_stop)
        assert hasattr(model, "trailing_stop_limit") and callable(
            model.trailing_stop_limit
        )
        assert hasattr(model, "stop_loss_and_limit") and callable(
            model.stop_loss_and_limit
        )
        assert hasattr(model, "settle_position") and callable(model.settle_position)

    @given(st.builds(RequestOrder))
    def test_market(self, model):
        m = model.market()
        assert m.descr.ordertype == KOrderTypeModel.market

    @given(st.builds(RequestOrder))
    def test_limit(self, model):
        m = model.limit(limit_price=42)
        assert m.descr.ordertype == KOrderTypeModel.limit
        assert m.descr.price == 42

    @given(st.builds(RequestOrder))
    def test_stop_loss(self, model):
        m = model.stop_loss(stop_loss_price=51)
        assert m.descr.ordertype == KOrderTypeModel.stop_loss
        assert m.descr.price == 51

    # TODO : MORE !

    # def test_cancel(self):
    #     raise NotImplementedError
    #     m = self.model.cancel()
    #     assert False  # TODO : smthg...


class TestRequestOrderNoPrice(unittest.TestCase):

    @given(RequestOrderNoPriceStrategy())
    def test_model(self, model):
        assert isinstance(model, RequestOrderNoPrice)

    @given(RequestOrderFinalizeStrategy(strategy=RequestOrderNoPriceStrategy()))
    def test_finalize(self, model):
        assert isinstance(model, RequestOrderNoPriceFinalized)


class TestRequestOrderOnePrice(unittest.TestCase):

    @given(RequestOrderOnePriceStrategy())
    def test_model(self, model):
        assert isinstance(model, RequestOrderOnePrice)

    @given(RequestOrderFinalizeStrategy(strategy=RequestOrderOnePriceStrategy()))
    def test_finalize(self, model):
        assert isinstance(model, RequestOrderOnePriceFinalized)


class TestRequestOrderTwoPrice(unittest.TestCase):

    @given(RequestOrderTwoPriceStrategy())
    def test_model(self, model):
        assert isinstance(model, RequestOrderTwoPrice)

    @given(RequestOrderFinalizeStrategy(strategy=RequestOrderTwoPriceStrategy()))
    def test_finalize(self, model):
        assert isinstance(model, RequestOrderTwoPriceFinalized)


# class TestRequestOrderSchema(unittest.TestCase):
#
#     def setUp(self) -> None:
#         self.schema = RequestOrderSchema()
#         self.descr_schema = self.schema.fields.get('descr').nested
#
#     @given(RequestOrderStrategy())
#     def test_dump_ok(self, model):
#         """ Verifying that expected data parses properly """
#         serialized = self.schema.dump(model)
#         expected = {
#             "volume": model.volume,
#             "pair": PairField().serialize('v', {'v': model.pair}),
#             "descr": KOrderDescrSchema().dump(model.descr),
#             "validate": True,
#             "userref": model.userref
#         }
#         if model.relative_starttm:  #if not expired
#             expected.update({"relative_starttm": TimerField().serialize('v', {'v': model.relative_starttm})})
#         if model.relative_expiretm:  #if not expired
#             expected.update({"relative_expiretm": TimerField().serialize('v', {'v': model.relative_expiretm})})
#         # check equality on dicts with usual python types, but display strings.
#         assert serialized == expected, print(str(serialized) + '\n' + str(expected))
#
#     @given(RequestOrderDictStrategy())
#     def test_load_ok(self, model):
#         ro = self.schema.load(model)
#         assert isinstance(ro, RequestOrderModel)
#
#     def test_load_fail(self):
#         # corrupted data:
#         wrg_orderstr = '{}'
#         # checking it actually fails
#         with self.assertRaises(Exception) as e:
#             self.schema.load(wrg_orderstr)

