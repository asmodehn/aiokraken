import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from aiokraken.rest.schemas.balance import BalanceStrategy, BalanceSchema, KDictStrategy, Balance
from aiokraken.rest.exceptions import AIOKrakenException
from hypothesis import given, settings, Verbosity

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestBalance(unittest.TestCase):

    #@settings(verbosity=Verbosity.verbose)
    @given(BalanceStrategy())
    def test_model(self, model):
        assert isinstance(model.accounts, dict)
        for n, a in model.accounts.items():
            assert isinstance(n, str)
            assert isinstance(a, Decimal)


class TestBalanceSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = BalanceSchema()

    #@settings(verbosity=Verbosity.verbose)
    @given(
        KDictStrategy( BalanceStrategy()))
    def test_deserialize(self, modeldict):
        a = self.schema.load(modeldict)
        assert isinstance(a, Balance)

    #@settings(verbosity=Verbosity.verbose)
    @given(BalanceStrategy())
    def test_serialize(self, model):
        d = self.schema.dump(model)
        for n, a in model.accounts.items():
            assert n in d, d
            assert a == d.get(n), d.get(n)