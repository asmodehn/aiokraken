import time
import unittest

import typing
from hypothesis import given
from parameterized import parameterized
import json
import marshmallow
import decimal

from ..ktm import TMModel, TimerField
from ..kabtype import KABTypeModel
from ..kordertype import KOrderTypeModel
from ..kopenorder import (KOpenOrderSchema, KOpenOrderModel,
KOrderDescrNoPriceFinalized,
KOrderDescrOnePriceFinalized,
KOrderDescrTwoPriceFinalized,
    OpenOrderStrategy, OpenOrderDictStrategy)
from ..korderdescr import KOrderDescrSchema
from ...exceptions import AIOKrakenException

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestOpenOrderModel(unittest.TestCase):

    @given(OpenOrderStrategy())
    def test_init(self, openorder):
        assert isinstance(openorder.cost, decimal.Decimal)
        assert isinstance(openorder.descr, (KOrderDescrNoPriceFinalized,
           KOrderDescrOnePriceFinalized,
           KOrderDescrTwoPriceFinalized))
        assert isinstance(openorder.expiretm, TMModel)
        assert isinstance(openorder.fee, decimal.Decimal)
        assert isinstance(openorder.limitprice, decimal.Decimal)
        assert isinstance(openorder.opentm, TMModel)
        assert isinstance(openorder.price, decimal.Decimal)
        assert isinstance(openorder.starttm, TMModel)
        assert isinstance(openorder.stopprice, decimal.Decimal)
        assert isinstance(openorder.vol, decimal.Decimal)
        assert isinstance(openorder.vol_exec, decimal.Decimal)
        # TODO : improve


class TestOpenOrderSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = KOpenOrderSchema()

    @given(OpenOrderStrategy())
    def test_dump_ok(self, model):
        """ Verifying that expected data parses properly """
        serialized = self.schema.dump(model)
        expected = {
            "descr": KOrderDescrSchema().dump(model.descr),
            "fee": "{0:f}".format(model.fee),
            "misc": model.misc,
            "oflags": model.oflags,
            "status": model.status,
            "refid": model.refid,
            "vol_exec": "{0:f}".format(model.vol_exec),
            "vol": "{0:f}".format(model.vol),
            "userref": model.userref,
            "expiretm": TimerField().serialize('v', {'v': model.expiretm}),
            "trades": model.trades
        }
        expected["limitprice"] = "{0:f}".format(model.limitprice)
        expected["cost"] = "{0:f}".format(model.cost)
        expected["stopprice"] = "{0:f}".format(model.stopprice)
        expected["opentm"] = TimerField().serialize('v', {'v': model.opentm})
        expected["starttm"] = TimerField().serialize('v', {'v': model.starttm})
        expected["price"] = "{0:f}".format(model.price)

        # check equality on dicts with usual python types, but display strings.
        assert serialized == expected, print(str(serialized) + '\n' + str(expected))

   # Note : Marshmallow design assumes model is always correct, therefore dump is not meant to fail...
    # Testing for this seems redundant.
    # load() should be used to parse unknown data structure, internal is assumed correct (typechecks !)

    @given(OpenOrderDictStrategy())
    def test_load_ok(self, model):
        oo = self.schema.load(model)
        assert isinstance(oo, KOpenOrderModel)


    def test_load_fail(self):
        # corrupted data:
        wrg_orderstr = '{"refid": null, "userref": 0, "status": "open", "opentm": 1571150298.798, ' \
                       '"starttm": 0, "expiretm": 1571150313, "descr": ' \
                       '{"pair": "XBTEUR", "type": "sell", "ordertype": "limit", "price": "11330.1", "price2": "0", "leverage": "none", "order": "sell 0.01000000 XBTEUR @ limit 11330.1","close":""},' \
                       '"vol":"0.01000000","vol_exec":"0.00000000","cost":"0.00000","fee":"0.00000","price":"0.00000","stopprice":"0.00000","limitprice":"0.00000","misc":"","oflags":"fciq"}}}}'
        # checking it actually fails
        with self.assertRaises(Exception) as e:
            self.schema.load(wrg_orderstr)

    # TODO : add more tests for specific errors we want to cover...