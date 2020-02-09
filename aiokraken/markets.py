import asyncio
import time
from collections import OrderedDict
from collections.abc import Mapping


import typing
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from aiokraken.model.asset import Asset

from aiokraken.marketdata import MarketData
from aiokraken.model.assetpair import AssetPair
from aiokraken.orders import Orders
from aiokraken.trades import Trades

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from aiokraken.rest.client import RestClient

from aiokraken.rest.schemas.krequestorder import RequestOrder
from aiokraken.rest.schemas.kopenorder import KOpenOrderModel
from aiokraken.rest.schemas.korderdescr import KOrderDescrOnePrice, KOrderDescr
from aiokraken.utils.filter import Filter

LOGGER = get_kraken_logger(__name__)


# TODO : unicity of the class in the semantics here (we connect to one exchange only)
#  => use module and setup on import, instead of class ?? Think about (Functional) Domain Model Representation...
#  Remember : python is better as a set of fancy scripts.
# TODO : favor immutability (see pyrsistent)
class Markets(Mapping):

    _filter: Filter
    details: typing.Dict[str, AssetPair]  # These are interesting for the developer,
    # but most should be implicit for user of aiokraken -> no need to make it easy to use.
    updated: datetime    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??
    validtime: timedelta

    impl: typing.Dict[str, MarketData]  # These are supposed to be used regularly

    trades: Trades

    orders: Orders

    # TODO : orders and positions should probably be here, just like trades...
    #  Even if we offer a filtered version in marketdata, this instance is supposed to manage the updates.

    def __init__(self, restclient: RestClient = None, valid_time: timedelta = None):
        self._filter = Filter(blacklist=[])
        self.restclient = RestClient() if restclient is None else restclient  # default restclient is possible here, but only usable for public requests...
        self.validtime = valid_time   # None means always valid

        self.impl = dict()
        self.trades = Trades(restclient=self.restclient)
        self.orders = Orders(restclient=self.restclient)

    def filter(self,  whitelist=None, blacklist=None, default_allow = True):
        """
        interactive filtering of the instance
        :return:
        """
        f = Filter(whitelist=whitelist, blacklist=blacklist, default_allow=default_allow)
        self._filter = self._filter + f

    async def __call__(self):
        """
        Trigger the actual retrieval of the market details, through the rest client.
        :param rest_client: optional
        # TODO: refresh this periodically ?
        :return:
        """
        if self._filter.whitelist:
            self.details = await self.restclient.assetpairs(pairs=self._filter.whitelist)()
        else:
            self.details = await self.restclient.assetpairs()()

        # also initializes trades and orders
        # TODO : each should work as "call by need" would do : requests only when needed...

        # CAREFUL : this requires private client
        # TODO : making it obvious in design somehow ???
        #   maybe split this into another class ("Exchange" ??)
        await self.trades()
        await self.orders()

        return self

    # TODO : howto make display to string / repr ??


    # TODO : https://www.janushenderson.com/en-us/investor/planning/calculate-average-cost/
    def tradecost(self, asset: Asset, amount: Decimal):
        from aiokraken.rest.schemas.kabtype import KABTypeModel
        # calculate the cost of the amount passed in param => go back in history but stop as soon as we reach the requested amount.
        # NOTE : trades are by default in reverse time order. IMPORTANT !
        # build cost structure from relevant trades
        cost = OrderedDict()  # ordered by time (towards hte past)
        total = Decimal()
        for tx, t in self.trades.items():
            p = None
            # figure out the pair for this trade:
            try:
                p = self.details[t.pair]
            except KeyError as ke:
                pn = {kp.altname: n for n, kp in self.details.items()}.get(t.pair)
                try:
                    p = self.details[pn]
                except Exception as e:
                    print(f" {e}: pair from trade not found in list of pair, cancelling tradecost computation")
            if p is not None:  # TODO :maybe filter useless pairs ealier ??
                if t.type is KABTypeModel.sell and p.quote in [asset.restname, asset.altname]:
                    if total + t.cost - t.fee > amount:
                        # only take part of it into account
                        cost[p.base] = cost.get(p.base, Decimal()) + t.vol * (amount - total) / (t.cost - t.fee)
                        total = amount  # no need to redo computation here (careful with precision !)
                        break
                    else:
                        cost[p.base] = cost.get(p.base, Decimal()) + t.vol
                        total = total + t.cost - t.fee
                elif t.type is KABTypeModel.buy and p.base in [asset.restname, asset.altname]:
                    if total + t.vol > amount:
                        # only take part of it into account
                        cost[p.quote] = cost.get(p.quote, Decimal()) + (t.cost - t.fee) * (amount - total) / (t.vol)
                        total = amount  # no need to redo computation (careful with precisoin !)
                        break
                    else:
                        cost[p.quote] = cost.get(p.quote, Decimal()) + t.cost - t.fee  # CAREFUL curerncy units : from doc, cost and fee are in quote currency
                        total = total + t.vol
            if total >= amount:  # TODO : careful about precision here !!!
                break  #finished !
        # TODO : if total  < amount we finished loop prematurely ? need to download more trade history ??
        return cost

    def __getitem__(self, key):
        def initdata(key):  # TODO : maybe some filtering based on pairs and data : market that are not volatile enough to cover fees should probably be skipped...
            self.impl.setdefault(key, MarketData(pair=self.details[key], restclient=self.restclient))  # instantiate if needed
            return self.impl[key]

        if (key in self._filter.whitelist) or self._filter.default:
            if key in self.details:
                return initdata(key)
            else:
                # we need to be able to query by altname as well
                revdict = {p.altname: n for n, p in self.details.items()}
                if key in revdict:
                    return initdata(revdict[key])
                else:
                    raise KeyError(f"{key} is not a pair name nor an altname")
        else:
            raise KeyError(f"{key} is a blacklisted Asset and is not accessible.")

    def __iter__(self):
        return iter(self.details.keys())

    def __len__(self):
        return len(self.details)


if __name__ == '__main__':

    mkts = Markets()

    async def assetpairs_retrieve_nosession():
        await mkts()
        for k, p in mkts.items():
            print(f" - {k}: {p}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(assetpairs_retrieve_nosession())
    time.sleep(1)

    loop.run_until_complete(assetpairs_retrieve_nosession())

    loop.close()


