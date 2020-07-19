import unittest

from aiokraken.websockets.schemas.tests.strats.st_owntrade import st_owntradews, st_owntradewsdict

from aiokraken.websockets.schemas.owntrades import ownTradeWS, ownTradeWSContentSchema, ownTradeWSSchema

from hypothesis import given


class TestownTrade(unittest.TestCase):

    @given(trd = st_owntradews())
    def test_valid_strategy(self, trd):
        assert isinstance(trd, ownTradeWS)

        assert isinstance(trd.ordertxid, str)
        assert isinstance(trd.postxid, str)
        assert isinstance(trd.pair, str)
        assert isinstance(trd.time, float)
        assert isinstance(trd.type, str)
        assert isinstance(trd.ordertype, str)
        assert isinstance(trd.price, float)
        assert isinstance(trd.cost, float)
        assert isinstance(trd.fee, float)
        assert isinstance(trd.vol, float)
        assert isinstance(trd.margin, float)
        assert trd.posstatus is None or isinstance(trd.posstatus, str)
        # assert isinstance(trd.pairname, typing.Optional[str])  # todo test this

    @given(dtrd = st_owntradewsdict())
    def test_valid_dictstrategy(self, dtrd):

        sch = ownTradeWSContentSchema()
        inst = sch.load(dtrd)
        assert isinstance(inst, ownTradeWS)


# TODO : test payload as well...

if __name__ == '__main__':
    unittest.main()
