import typing
from datetime import timedelta

from aiokraken import RestClient

from aiokraken.rest.schemas.ktrade import KTradeModel


class Trades:
    """ Note : This is the monad / mutable state, providing an "imperative" interface to immutable data.
        There fore it should act as a container, on the time axis... probably via the callable / iterator protocols
    """
    impl: typing.Dict[str, KTradeModel]  # (filtered/market related) trade history. TODO : find out when to retrieve new. how do we know about orders ??

    def __init__(self, restclient: RestClient = None, valid_time: timedelta = None):
        self.restclient = restclient or RestClient()  # default restclient is possible here, but only usable for public requests...
        self.validtime = valid_time   # None means always valid
        self.impl = dict()  # Need async call : raii is not doable here... unless we have a separate async constructor ?

    def query(self):
        # TODO : interface to query trades request
        raise NotImplementedError

    async def __call__(self):  # TODO : pass necessary parameters
        """
        This is a call mutating this object. GOAL : updating trades out of the view of the user
        (contained datastructures change by themselves, from REST calls or websockets callback...)
        """
        new_trades = (await self.restclient.trades(offset=0)())

        # TODO : manage offsets here... (or in caller ?)

        if new_trades:
            self.impl.update(new_trades)  # this will aggregate all trades...

        return self

    def items(self):  # TODO : what is our interface here, simply mapping ???
        return self.impl.items()

    def __getitem__(self, item):
        return self.impl[item]

    def __iter__(self):
        return iter(self.impl)

    def __len__(self):
        return len(self.impl)


async def trades():  # async constructor, to enable RAII for this class - think directed container in time, extracting more data from the now...
    pass  # TODO !!!!


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

        # TODO : this should probably be done out of sight...
        #emas_1m = emas_1m(ohlc_1m.model)  # explicit update of indicator for this timeframe
        # TODO ohlc.ema(name="EMA_12", length=12) maybe ??

    loop = asyncio.get_event_loop()

    assert len(trades) == 0

    loop.run_until_complete(trades_retrieve_nosession())
    assert len(trades) >0

    # REMINDER : This must remain safe for the user : do not create any orders.
    # Rely on integration tests to validate merging of data.

    loop.close()

