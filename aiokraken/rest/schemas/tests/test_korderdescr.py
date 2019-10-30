import time
import unittest
from decimal import Decimal
from dataclasses import asdict

from parameterized import parameterized
import json
import marshmallow
import decimal
from hypothesis import given, settings, Verbosity, strategies as st

from ..kabtype import KABTypeModel
from ..kordertype import KOrderTypeModel
from ..kpair import PairModel
from ..korderdescr import (
    KOrderDescr,
    KOrderDescrStrategy,
    KOrderDescrNoPrice,
    KOrderDescrNoPriceFinalized,
    KOrderDescrNoPriceStrategy,
    KOrderDescrOnePrice,
    KOrderDescrOnePriceFinalized,
    KOrderDescrOnePriceStrategy,
    KOrderDescrTwoPrice,
    KOrderDescrTwoPriceFinalized,
    KOrderDescrTwoPriceStrategy,
    KOrderDescrFinalizeStrategy,
    KDictStrategy,
    KOrderDescrSchema,
    KOrderDescrCloseSchema,
)
from ...exceptions import AIOKrakenException

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestOrderDescr(unittest.TestCase):

    @settings(verbosity=Verbosity.verbose)
    @given(KOrderDescrStrategy())
    def test_model(self, model):
        assert isinstance(model, KOrderDescr)
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


class TestOrderDescr_NoPrice(unittest.TestCase):
    @settings(verbosity=Verbosity.verbose)
    @given(KOrderDescrNoPriceStrategy())
    def test_model(self, model):
        assert isinstance(model, KOrderDescrNoPrice)
        assert hasattr(model, "pair") and isinstance(model.pair, PairModel)
        assert hasattr(model, "ordertype") and isinstance(
            model.ordertype, KOrderTypeModel
        )

        assert hasattr(model, "buy") and callable(model.buy)
        assert hasattr(model, "sell") and callable(model.sell)

    @settings(verbosity=Verbosity.verbose)
    @given(KOrderDescrFinalizeStrategy(strategy=KOrderDescrNoPriceStrategy()))
    def test_finalize(self, model):
        assert isinstance(model, KOrderDescrNoPriceFinalized)
        assert hasattr(model, "pair") and isinstance(model.pair, PairModel)
        assert hasattr(model, "ordertype") and isinstance(
            model.ordertype, KOrderTypeModel
        )
        assert hasattr(model, "abtype") and isinstance(model.abtype, KABTypeModel)
        assert hasattr(model, "close") and isinstance(
            model.close,
            (type(None), KOrderDescrNoPrice, KOrderDescrOnePrice, KOrderDescrTwoPrice),
        )


class TestOrderDescr_OnePrice(unittest.TestCase):
    @settings(verbosity=Verbosity.verbose)
    @given(KOrderDescrOnePriceStrategy())
    def test_model(self, model):
        assert isinstance(model, KOrderDescrOnePrice)
        assert hasattr(model, "pair") and isinstance(model.pair, PairModel)
        assert hasattr(model, "ordertype") and isinstance(
            model.ordertype, KOrderTypeModel
        )
        assert hasattr(model, "price") and isinstance(model.price, Decimal)
        assert hasattr(model, "buy") and callable(model.buy)
        assert hasattr(model, "sell") and callable(model.sell)

    @settings(verbosity=Verbosity.verbose)
    @given(KOrderDescrFinalizeStrategy(strategy=KOrderDescrOnePriceStrategy()))
    def test_finalize(self, model):
        assert isinstance(model, KOrderDescrOnePriceFinalized)
        assert hasattr(model, "pair") and isinstance(model.pair, PairModel)
        assert hasattr(model, "ordertype") and isinstance(
            model.ordertype, KOrderTypeModel
        )
        assert hasattr(model, "price") and isinstance(model.price, Decimal)
        assert hasattr(model, "abtype") and isinstance(model.abtype, KABTypeModel)
        assert hasattr(model, "close") and isinstance(
            model.close,
            (type(None), KOrderDescrNoPrice, KOrderDescrOnePrice, KOrderDescrTwoPrice),
        )


class TestOrderDescr_TwoPrice(unittest.TestCase):
    @given(KOrderDescrTwoPriceStrategy())
    def test_model(self, model):
        assert isinstance(model, KOrderDescrTwoPrice)
        assert hasattr(model, "pair") and isinstance(model.pair, PairModel)
        assert hasattr(model, "ordertype") and isinstance(
            model.ordertype, KOrderTypeModel
        )
        assert hasattr(model, "price") and isinstance(model.price, Decimal)
        assert hasattr(model, "price2") and isinstance(model.price, Decimal)
        assert hasattr(model, "buy") and callable(model.buy)
        assert hasattr(model, "sell") and callable(model.sell)

    @given(KOrderDescrFinalizeStrategy(strategy=KOrderDescrTwoPriceStrategy()))
    def test_finalize(self, model):
        assert isinstance(model, KOrderDescrTwoPriceFinalized)
        assert hasattr(model, "pair") and isinstance(model.pair, PairModel)
        assert hasattr(model, "ordertype") and isinstance(
            model.ordertype, KOrderTypeModel
        )
        assert hasattr(model, "price") and isinstance(model.price, Decimal)
        assert hasattr(model, "price2") and isinstance(model.price, Decimal)
        assert hasattr(model, "abtype") and isinstance(model.abtype, KABTypeModel)

        assert hasattr(model, "close") and isinstance(
            model.close,
            (type(None), KOrderDescrNoPrice, KOrderDescrOnePrice, KOrderDescrTwoPrice),
        )


class TestOrderDescrSchema(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = KOrderDescrSchema()

    @settings(verbosity=Verbosity.verbose)
    @given(
        KDictStrategy(
            st.one_of(
                KOrderDescrFinalizeStrategy(strategy=KOrderDescrNoPriceStrategy()),
                KOrderDescrFinalizeStrategy(strategy=KOrderDescrOnePriceStrategy()),
                KOrderDescrFinalizeStrategy(strategy=KOrderDescrTwoPriceStrategy()),
            )
        )
    )
    def test_load_ok(self, orderdescrdct):
        p = self.schema.load(orderdescrdct)
        assert isinstance(
            p,
            (
                KOrderDescrNoPriceFinalized,
                KOrderDescrOnePriceFinalized,
                KOrderDescrTwoPriceFinalized,
            ),
        )

    # TODO :validate deserialize fail on unexpected / incomplete data...

    @settings(verbosity=Verbosity.verbose)
    @given(
        st.one_of(
            [
                KOrderDescrFinalizeStrategy(strategy=KOrderDescrNoPriceStrategy()),
                KOrderDescrFinalizeStrategy(strategy=KOrderDescrOnePriceStrategy()),
                KOrderDescrFinalizeStrategy(strategy=KOrderDescrTwoPriceStrategy()),
            ]
        )
    )
    def test_dump_ok(self, orderdescrmodel):
        p = self.schema.dump(orderdescrmodel)
        assert isinstance(p, dict)
        expected = {k: v for k, v in asdict(orderdescrmodel).items() if v is not None}
        expected.pop("abtype")  # no abtype !
        expected["pair"] = str(orderdescrmodel.pair)
        expected["type"] = orderdescrmodel.abtype.value
        expected["ordertype"] = orderdescrmodel.ordertype.value
        expected["leverage"] = "{0:f}".format(orderdescrmodel.leverage)

        if orderdescrmodel.close:
            expected["close"] = KOrderDescrCloseSchema().dump(orderdescrmodel.close)

        if hasattr(orderdescrmodel, "price"):
            expected["price"] = "{0:f}".format(orderdescrmodel.price)
        if hasattr(orderdescrmodel, "price2"):
            expected["price2"] = "{0:f}".format(
                orderdescrmodel.price2
            )  # careful with exponents on decimal https://stackoverflow.com/a/27053722
        assert p == expected, print(str(p) + "\n" + str(expected))

    @settings(verbosity=Verbosity.verbose)
    @given(
        st.one_of(
            [
                KOrderDescrNoPriceStrategy(),
                KOrderDescrOnePriceStrategy(),
                KOrderDescrTwoPriceStrategy(),
            ]
        )
    )
    def test_dump_fail(self, non_finalized_model):
        """ must fail on non finalized descr """

        with self.assertRaises(Exception) as e:
            p = self.schema.dump(non_finalized_model)
            # TODO: refine

    # TODO : more corrupted data