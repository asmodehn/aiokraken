import time
import unittest

import typing

from aiokraken.rest.schemas.ktrade import KTradeStrategy, KTradeSchema, TradeDictStrategy, KTradeModel
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


class TestTradeModel(unittest.TestCase):

    @given(KTradeStrategy())
    def test_init(self, trade):
        assert isinstance(trade.ordertxid, str)  # order responsible for execution of trade
        assert isinstance(trade.postxid, str)  # order responsible for execution of trade
        assert isinstance(trade.pair, str)  # asset pair
        assert isinstance(trade.time, int)  # unix timestamp of trade
        assert isinstance(trade.type, KABTypeModel)  # type of order (buy/sell)
        assert isinstance(trade.ordertype, KOrderTypeModel)  # order type
        assert isinstance(trade.price, decimal.Decimal)  # average price order was executed at (quote currency)
        assert isinstance(trade.cost, decimal.Decimal)  # total cost of order (quote currency)
        assert isinstance(trade.fee, decimal.Decimal)  # total fee (quote currency)
        assert isinstance(trade.vol, decimal.Decimal)  # volume (base currency)
        assert isinstance(trade.margin, decimal.Decimal)  # initial margin (quote currency)
        assert isinstance(trade.misc,  str)  # comma delimited list of miscellaneous info
        # TODO : improve


class TestTradeSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = KTradeSchema()

    @given(KTradeStrategy())
    def test_dump_ok(self, model):
        """ Verifying that expected data parses properly """
        serialized = self.schema.dump(model)
        expected = {

            "ordertxid": model.ordertxid,  # order responsible for execution of trade
            "postxid": model.postxid,
            "pair": model.pair,  # asset pair
            "time": model.time,  # unix timestamp of trade
            "type": model.type.value,  # type of order (buy/sell)
            "ordertype": model.ordertype.value,  # order type
            "price": "{0:f}".format(model.price),  # average price order was executed at (quote currency)
            "cost": "{0:f}".format(model.cost),  # total cost of order (quote currency)
            "fee": "{0:f}".format(model.fee),  # total fee (quote currency)
            "vol": "{0:f}".format(model.vol),  # volume (base currency)
            "margin": "{0:f}".format(model.margin),  # initial margin (quote currency)
            "misc": model.misc,  # comma delimited list of miscellaneous info

            "posstatus": model.posstatus,
        }

        # check equality on dicts with usual python types, but display strings.
        assert serialized == expected, print(str(serialized) + '\n' + str(expected))

   # Note : Marshmallow design assumes model is always correct, therefore dump is not meant to fail...
    # Testing for this seems redundant.
    # load() should be used to parse unknown data structure, internal is assumed correct (typechecks !)

    @given(TradeDictStrategy())
    def test_load_ok(self, model):
        oo = self.schema.load(model)
        assert isinstance(oo, KTradeModel)

    # TODO
    # def test_load_fail(self):
    #     # corrupted data:
    #     wrg_tradestr = '{"refid": null, "userref": 0, "status": "open", "opentm": 1571150298.798, ' \
    #                    '"starttm": 0, "expiretm": 1571150313, "descr": ' \
    #                    '{"pair": "XBTEUR", "type": "sell", "ordertype": "limit", "price": "11330.1", "price2": "0", "leverage": "none", "order": "sell 0.01000000 XBTEUR @ limit 11330.1","close":""},' \
    #                    '"vol":"0.01000000","vol_exec":"0.00000000","cost":"0.00000","fee":"0.00000","price":"0.00000","stopprice":"0.00000","limitprice":"0.00000","misc":"","oflags":"fciq"}}}}'
    #     # checking it actually fails
    #     with self.assertRaises(Exception) as e:
    #         self.schema.load(wrg_tradestr)

    # TODO : add more tests for specific errors we want to cover...