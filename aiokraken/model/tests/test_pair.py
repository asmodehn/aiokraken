import unittest

from hypothesis import given

from aiokraken.model.tests.strats.st_pair import PairStrategy


class TestPairModel(unittest.TestCase):

    @given(PairStrategy())
    def test_repr(self, model):
        assert repr(model) == f"{repr(model.base)}/{repr(model.quote)}"

    @given(PairStrategy())
    def test_str(self, model):
        assert str(model) == f"{model.base}{model.quote}"


if __name__ == "__main__":
    unittest.main()