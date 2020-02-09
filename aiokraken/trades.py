import typing
from collections import OrderedDict
from datetime import timedelta, datetime
from types import MappingProxyType

from aiokraken import RestClient

from aiokraken.rest.schemas.ktrade import KTradeModel


class Trades:
    """ Note : This is the monad / mutable state, providing an "imperative" interface to immutable data.
        There fore it should act as a container, on the (reversed) time axis...
    """
    # should work since 3.7.2 :
    # Ref : https://docs.python.org/3/library/typing.html#typing.OrderedDict
    impl: typing.OrderedDict[str, KTradeModel]  # (filtered/market related) trade history. TODO : find out when to retrieve new. how do we know about orders ??

    def __init__(self, trade_history: OrderedDict = None, restclient: RestClient = None):
        self.restclient = restclient
        if self.restclient is None:
            self.impl = MappingProxyType(trade_history)
        else:
            self.impl = trade_history if trade_history is not None else OrderedDict()  # Need async call : raii is not doable here... unless we have a separate async constructor ?
        # TODO : mapping proxy to avoid mutation problems ?

    def query(self):
        # TODO : interface to query trades request
        raise NotImplementedError

    async def __call__(self, start: datetime = None, end: datetime = None):  # TODO : pass necessary parameters (cf trades request)
        """
        This is a call mutating this object. GOAL : updating trades out of the view of the user
        (contained datastructures change by themselves, from REST calls or websockets callback...)
        """

        timeinterval = {}
        if start is not None:
            timeinterval['start'] = int(start.timestamp())
        if end is not None:
            timeinterval['end'] = int(start.timestamp())

        if self.restclient is not None:
            # Here we check our local knowledge is uptodate

            # time interval
            current = self
            if start is not None:
                current = current.from_datetime(start)
            if end is not None:
                current = current.to_datetime(end)

            new_trades, count = (await self.restclient.trades(offset=len(current), **timeinterval)())

            # we retrieve all matching trades... (eager on count & lazy on times)
            while new_trades and count > len(self.impl):
                self.impl.update(new_trades)  # this will aggregate all trades for time time interval...

                # time interval
                current = self
                if start is not None:
                    current = current.from_datetime(start)
                if end is not None:
                    current = current.to_datetime(end)

                new_trades, count = (
                    await self.restclient.trades(offset=len(current), **timeinterval)())

        # ELSE if there is no client, it means this instance is supposed to be just a proxy on the mutating data.
        # OR WE want to make a specific class ??? Probably AFTER doing the timeindexed dataframe for trades.

        # we keep aggregating in place on the same object
        return self

    def items(self):  # TODO : what is our interface here, simply mapping ???
        return self.impl.items()

    def from_datetime(self, start: datetime):

        res = OrderedDict({
            tx: t for tx, t in self.impl.items() if int(start.timestamp()) < t.time
        })

        return Trades(trade_history=res)

    def to_datetime(self, stop: datetime):
        res = OrderedDict({
            tx: t for tx, t in self.impl.items() if t.time < int(stop.timestamp())
        })

        return Trades(trade_history=res)

    def __getitem__(self, item):
        if item in self.impl:
            return self.impl[item]

    def __len__(self):
        return len(self.impl)


# class TradesProxy:
#
#     _impl: MappingProxyType[str, KTradeModel]
#     _origin: Trades
#
#     def __init__(self, trades_history: OrderedDict):
#         self._impl = MappingProxyType(trades_history)
#
#     async def __aiter__(self):
#         while True:
#             lastlen = len(self._origin)
#             for t in self._impl:
#                 yield t
#             await self._origin()  # tentative call
#             if len(self._origin) <= lastlen:
#                 break  # exit the loop if there was no new data
#         await self._origin()


async def trades(restclient: RestClient):
    # async constructor, to enable RAII for this class - think directed container in time, extracting more data from the now...
    t = Trades(restclient=restclient)
    return await t()  # RAII()
    # TODO : return a proxy instead...

if __name__ == '__main__':
    import time
    import asyncio
    from aiokraken.rest.client import RestClient
    from aiokraken.rest.api import Server
    from aiokraken.config import load_api_keyfile

    keystruct = load_api_keyfile()

    # Client can be global: there is only one.
    rest = RestClient(server=Server(key=keystruct.get('key'),
                                    secret=keystruct.get('secret')))

    # ohlc data can be global (one per market*timeframe only)
    trades = Trades(restclient=rest)

    async def trades_retrieve_nosession():
        global rest, trades
        await trades()
        for txid, t in trades.items():
            print(f" - {txid}: {t}")

    loop = asyncio.get_event_loop()

    assert len(trades) == 0

    loop.run_until_complete(trades_retrieve_nosession())
    assert len(trades) >0

    # REMINDER : This must remain safe for the user : do not create any orders.
    # Rely on integration tests to validate merging of data.

    loop.close()

