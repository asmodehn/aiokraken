import unittest

from hypothesis import given

from aiokraken.rest.schemas.kleverage import Leverage, LeverageField, LeverageStrategy, LeverageStringStrategy


class TestPairField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = LeverageField()

    @given(LeverageStringStrategy())
    def test_deserialize(self, pairstr):
        p = self.field.deserialize(pairstr)
        assert isinstance(p, Leverage)
        assert isinstance(p.a, int)
        assert isinstance(p.b, int)

    @given(LeverageStrategy())
    def test_serialize(self, lvrg):
        p = self.field.serialize('leverage', {'leverage': lvrg})
        assert p == str(lvrg), p

