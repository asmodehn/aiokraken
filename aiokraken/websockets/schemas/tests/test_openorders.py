import unittest

from aiokraken.websockets.schemas.openorders import (
    openOrderDescrWS, openOrderDescrWSSchema, openOrderWS, openOrderWSSchema,
)

from aiokraken.websockets.schemas.tests.strats.st_openorders import (
    st_openorderdescrws, st_openorderdescrwsdict,
    st_openorderws, st_openorderwsdict,
)

from hypothesis import given


class TestopenOrderDescr(unittest.TestCase):

    @given(ood = st_openorderdescrws())
    def test_valid_strategy(self, ood):
        assert isinstance(ood, openOrderDescrWS)

        assert isinstance(ood.pair, str)
        assert isinstance(ood.type, str)
        assert isinstance(ood.ordertype, str)
        assert isinstance(ood.price, float)
        assert isinstance(ood.price2, float)
        assert isinstance(ood.leverage, float)
        assert isinstance(ood.order, str)
        assert isinstance(ood.close, str)
        # assert isinstance(ood.position, typing.Optional[str])  # todo test this

    @given(odd = st_openorderdescrwsdict())
    def test_valid_dictstrategy(self, odd):

        sch = openOrderDescrWSSchema()
        inst = sch.load(odd)
        assert isinstance(inst, openOrderDescrWS)


class TestopenOrder(unittest.TestCase):

    @given(oo = st_openorderws())
    def test_valid_strategy(self, oo):
        assert isinstance(oo, openOrderWS)

        assert isinstance(oo.orderid, str)
        assert isinstance(oo.refid, str)
        assert isinstance(oo.userref, int)
        assert isinstance(oo.status, str)
        assert isinstance(oo.opentm, float)
        assert isinstance(oo.starttm, float)
        assert isinstance(oo.expiretm, float)
        assert isinstance(oo.descr, openOrderDescrWS)
        assert isinstance(oo.vol, float)
        assert isinstance(oo.vol_exec,  float)
        assert isinstance(oo.cost, float)
        assert isinstance(oo.fee, float)
        assert isinstance(oo.avg_price, float)
        assert isinstance(oo.stopprice, float)
        assert isinstance(oo.limitprice, float)
        assert isinstance(oo.misc, str)
        assert isinstance(oo.oflags, str)

        # assert isinstance(oo.orderid, typing.Optional[str])  # todo test this

    @given(ood = st_openorderwsdict())
    def test_valid_dictstrategy(self, ood):

        sch = openOrderWSSchema()
        inst = sch.load(ood)
        assert isinstance(inst, openOrderWS)


if __name__ == '__main__':
    unittest.main()
