import time
import unittest

import typing
from hypothesis import given
from parameterized import parameterized
import json
import marshmallow
import decimal

from aiokraken.rest.schemas.ktm import TMModel, TimerField
from aiokraken.rest.schemas.kclosedorder import (KClosedOrderSchema, KClosedOrderModel,
KOrderDescrNoPriceFinalized,
KOrderDescrOnePriceFinalized,
KOrderDescrTwoPriceFinalized,
    ClosedOrderStrategy, ClosedOrderDictStrategy)
from aiokraken.rest.schemas.korderdescr import KOrderDescrSchema
from aiokraken.rest.exceptions import AIOKrakenException

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestClosedOrderModel(unittest.TestCase):

    @given(ClosedOrderStrategy())
    def test_init(self, closedorder):
        assert isinstance(closedorder.cost, decimal.Decimal)
        assert isinstance(closedorder.descr, (KOrderDescrNoPriceFinalized,
                                              KOrderDescrOnePriceFinalized,
                                              KOrderDescrTwoPriceFinalized))
        assert isinstance(closedorder.expiretm, TMModel)
        assert isinstance(closedorder.fee, decimal.Decimal)
        assert isinstance(closedorder.limitprice, decimal.Decimal)
        assert isinstance(closedorder.opentm, TMModel)
        assert isinstance(closedorder.price, decimal.Decimal)
        assert isinstance(closedorder.starttm, TMModel)
        assert isinstance(closedorder.stopprice, decimal.Decimal)
        assert isinstance(closedorder.vol, decimal.Decimal)
        assert isinstance(closedorder.vol_exec, decimal.Decimal)
        # TODO : improve


class TestOpenOrderSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = KClosedOrderSchema()

    @given(ClosedOrderStrategy())
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
            "trades": model.trades,
            "reason": model.reason
        }
        expected["limitprice"] = "{0:f}".format(model.limitprice)
        expected["cost"] = "{0:f}".format(model.cost)
        expected["stopprice"] = "{0:f}".format(model.stopprice)
        expected["opentm"] = TimerField().serialize('v', {'v': model.opentm})
        expected["starttm"] = TimerField().serialize('v', {'v': model.starttm})
        expected["price"] = "{0:f}".format(model.price)
        expected["closetm"] = TimerField().serialize('v', {'v': model.closetm})

        # check equality on dicts with usual python types, but display strings.
        assert serialized == expected, print(str(serialized) + '\n' + str(expected))

   # Note : Marshmallow design assumes model is always correct, therefore dump is not meant to fail...
    # Testing for this seems redundant.
    # load() should be used to parse unknown data structure, internal is assumed correct (typechecks !)

    @given(ClosedOrderDictStrategy())
    def test_load_ok(self, model):
        oo = self.schema.load(model)
        assert isinstance(oo, KClosedOrderModel)


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