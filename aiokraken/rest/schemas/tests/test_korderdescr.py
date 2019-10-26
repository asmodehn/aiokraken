import time
import unittest
from decimal import Decimal
from dataclasses import asdict

from parameterized import parameterized
import json
import marshmallow
import decimal
from hypothesis import given, settings, Verbosity, strategies as st

from ..korderdescr import KOrderDescrModel, KOrderDescrSchema, KOrderDescrStrategy, KOrderDescrDictStrategy
from ...exceptions import AIOKrakenException

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestOrderDescrModel(unittest.TestCase):

    @settings(verbosity=Verbosity.verbose)
    @given(KOrderDescrStrategy())
    def test_repr(self, model):
        assert model.order == f"{model.abtype} @ {model.price} {model.ordertype}"
        assert repr(model) == f"{model.pair}: {model.order}", print(repr(model) + '\n' + f"{model.order}")


class TestOrderDescrSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = KOrderDescrSchema()

    @given(KOrderDescrDictStrategy())
    def test_deserialize(self, orderdescrdct):
        p = self.schema.load(orderdescrdct)
        assert isinstance(p, KOrderDescrModel)

    @given(KOrderDescrStrategy())
    def test_serialize(self, orderdescrmodel):
        p = self.schema.dump(orderdescrmodel)
        assert isinstance(p, dict)
        expected = {k: v for k, v in asdict(orderdescrmodel).items() if v is not None}
        expected['pair'] = str(orderdescrmodel.pair)
        expected['abtype'] = orderdescrmodel.abtype.value
        expected['ordertype'] = orderdescrmodel.ordertype.value
        expected['leverage'] = "{0:f}".format(orderdescrmodel.leverage)

        if orderdescrmodel.price is not None:
            expected['price'] = "{0:f}".format(orderdescrmodel.price)
        if orderdescrmodel.price2 is not None:
            expected['price2'] = "{0:f}".format(orderdescrmodel.price2)  # careful with exponents on decimal https://stackoverflow.com/a/27053722
        assert p == expected, print(str(p) + '\n' + str(expected))

    # TODO : test invariant with serialize / deserialize and vice versa
