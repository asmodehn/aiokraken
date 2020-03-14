import typing
from collections import OrderedDict
from datetime import timedelta, datetime, timezone
from types import MappingProxyType

from aiokraken.model.assetpair import AssetPair

from aiokraken import RestClient

from aiokraken.rest.schemas.ktrade import KTradeModel


from aiokraken.model.tradeframe import TradeFrame, tradeframe


class Trades:
    """ Note : This is the monad / mutable state, providing an "imperative" interface to immutable data.
        There fore it should act as a container, on the (reversed) time axis...
    """
    model: typing.Optional[TradeFrame]

    @property
    def begin(self):
        return self.model.begin

    @property
    def end(self):
        return self.model.end

    def __init__(self, trade_history: OrderedDict = None, restclient: RestClient = None,  pair: typing.Union[AssetPair, str] = None, loop=None):
        #TODO : splittable by pair... (dual of ledger which is mergeable by asset)
        self.pair = pair  # TODO: None pair is "all" (API default)
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self.restclient = restclient

        self.model = None  # Need async call : raii is not doable here...

    def query(self):
        # TODO : interface to query trades request
        raise NotImplementedError

    async def __call__(self, start: datetime = None, stop: datetime = None):  # TODO : pass necessary parameters (cf trades request)
        """
        This is a call mutating this object. GOAL : updating trades out of the view of the user
        (contained datastructures change by themselves, from REST calls or websockets callback...)
        """

        if self.restclient is not None and (self.model is None or start < self.model.begin or stop > self.model.end):
            # we retrieve all matching trades... lazy on times !
            tradeshist, count = await self.restclient.trades(start=start, end=stop, offset=0)

            # loop until we get *everything*
            # Note : if this is too much, leverage local storage
            # TODO ! - in relation with time... assume past data doesnt change)
            #  or refine filters (time, etc.)
            while len(tradeshist) < count:
                # Note : here we recurse only one time. we need to recurse to respect ratelimit...
                more_tradeshist, count = await self.restclient.trades(start=start, end=stop, offset=len(tradeshist))
                tradeshist.update(more_tradeshist)

            model = tradeframe(tradehistory_as_dict=tradeshist)
            if model:
                self.model = model.value
            else:
                raise RuntimeError("Something went wrong")

        # we keep aggregating in place on the same object
        return self

    def __getitem__(self, item):
        # if isinstance(item, ledgertype):
        #     pass # TODO TYPE case
        if isinstance(item, datetime):
            return self.model[item]
        elif isinstance(item, slice):
            # check for slice of times
            if isinstance(item.start, datetime) and isinstance(item.stop, datetime):
                # Retrieve data if needed and block (sync)
                if self.model is None or item.start < self.model.begin or item.stop > self.model.end:
                    update_task = self.loop.create_task(
                        self(  # TODO : stitching to be managed like a cache (decorator around __call__)
                            start=min(item.start, self.model.begin) if self.model else item.start,
                            stop=max(item.stop, self.model.end) if self.model else item.stop
                        ))
                    self.loop.run_until_complete(update_task)  # run the task in background and sync block.

                return self.model[item.start:item.stop]

        else:  # anything else : rely on the model
            return self.model[item]

    def __len__(self):
        if self.model is not None:
            return len(self.model)
        else:
            return 0


# similar design as ledger...
async def trades( restclient: RestClient, begin: datetime = None, end: datetime = None) -> Trades:
    # async constructor, to enable RAII for this class - think directed container in time, extracting more data from the now...
    t = Trades(restclient=restclient)
    return await t(start=begin, stop=end)  # RAII()
    # TODO : return a proxy instead... => prevent accidental local modifications.


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

    # this retrieves (asynchronously and transparently) the data from the last week only
    now = datetime.now(tz=timezone.utc)
    for inf in trades[now - timedelta(weeks=1): now]:
        print(inf)

    # REMINDER : This must remain safe for the user : do not create any orders.
    # Rely on integration tests to validate merging of data.

