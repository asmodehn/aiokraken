import time
import unittest

import typing
from decimal import Decimal

from aiokraken.rest.schemas.kledger import KLedgerInfoStrategy, KLedgerInfoSchema, KLedgerInfoDictStrategy, KLedgerInfo

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


class TestLedgerInfo(unittest.TestCase):

    @given(KLedgerInfoStrategy())
    def test_init(self, ledger):
        assert isinstance(ledger.refid, str)  # reference id
        assert isinstance(ledger.time, int)  # unix timestamp of ledger
        assert isinstance(ledger.type, str)  # type of ledger entry
        assert isinstance(ledger.aclass, str)  # asset class
        assert isinstance(ledger.asset, str)  # asset
        assert isinstance(ledger.amount, Decimal)  # transaction amount
        assert isinstance(ledger.fee, Decimal)  # transaction fee
        assert isinstance(ledger.balance, Decimal)  # resulting balance
        #optionals
        assert ledger.ledger_id is None or isinstance(ledger.ledger_id, str)  # this will be set a bit after initialization

        # TODO : improve


class TestKLedgerInfoSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = KLedgerInfoSchema()

    @given(KLedgerInfoStrategy())
    def test_dump_ok(self, model):
        """ Verifying that expected data parses properly """
        serialized = self.schema.dump(model)
        expected = {

            "refid": model.refid,  # reference id
            "time": model.time,  # unix timestamp of trade
            "type": model.type,   # type of ledger entry
            "aclass": model.aclass,  # asset class
            "asset": model.asset,  # asset
            "amount": "{0:f}".format(model.amount),  # total cost of order (quote currency)
            "fee": "{0:f}".format(model.fee),  # total fee (quote currency)
            "balance": "{0:f}".format(model.balance),  # volume (base currency)
            "ledger_id": model.ledger_id,
        }

        # check equality on dicts with usual python types, but display strings.
        assert serialized == expected, print(str(serialized) + '\n' + str(expected))

   # Note : Marshmallow design assumes model is always correct, therefore dump is not meant to fail...
    # Testing for this seems redundant.
    # load() should be used to parse unknown data structure, internal is assumed correct (typechecks !)

    @given(KLedgerInfoDictStrategy())
    def test_load_ok(self, model):
        oo = self.schema.load(model)
        assert isinstance(oo, KLedgerInfo)

    # TODO : add more tests for specific errors we want to cover...