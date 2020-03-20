# TODO : self updating ledger...
import typing
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
import asyncio

from aiokraken.websockets.schemas.ticker import TickerWS as TickerModel

from aiokraken import WssClient

from aiokraken.model.assetpair import AssetPair

from aiokraken.model.asset import Asset

from aiokraken.rest import RestClient

from aiokraken.model.tickerframe import tickerframe, TickerFrame



class Ticker:
    """ Note : This is the monad / mutable state, providing an "imperative" interface to immutable data.
        There fore it should act as a container, on the (reversed) time axis...
    """
    model: typing.Optional[TickerFrame]
    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??

    @property
    def begin(self):
        return self.model.begin

    @property
    def end(self):
        return self.model.end

    def __init__(self,  restclient: RestClient, pair: typing.Union[AssetPair, str], wsclient: WssClient= None, loop = None):
        # We want all assets, or just one at a time. Note ledger instances are mergeable vertically on this...
        self.pair = pair  # one pair at a time, (but mergeable !)
        self.loop = loop if loop is not None else asyncio.get_event_loop()

        self.restclient = restclient
        # Note if Restclient is None, this is just a proxy,
        # it cannot update by itself, it doesnt really "contain" data.

        self.wsclient = wsclient if wsclient is not None else WssClient(loop=self.loop)
        # defaults to have a websocket client

        self.model = None  # Need async call : raii is not doable here...
        # TODO : mapping proxy to avoid mutation problems ?

    def _update(self, tkr: TickerWS):
        self.model(tkr)  # tickerframe update

    async def __call__(self):  # ticker request doesnt allow requesting for a specific time (use OHLC for this)
        # self update

        if self.restclient is not None and (self.model is None):
            # we retrieve all matching tickers... lazy on times !
            tickers = await self.restclient.ticker(pairs=[self.pair])

            model = tickerframe(tickers_as_dict=tickers)
            if model:
                self.model = model.value
            else:
                raise model.value

            # we got a response from REST, we can now subscribe to our topic via the websocket connection

            p = await self.restclient.validate_pair(pair=self.pair)

            if self.wsclient is not None:
                # TODO : prevent redundant subscription ?
                await self.wsclient.ticker(pairs=[self.pair], callback=self._update)

        # we keep aggregating in place on the same object
        return self

    # TODO : maybe a property per asset and per ledger type, to avoid abusing getitem

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

    async def __aiter__(self):
        # delegate to model
        if self.model is None:
            # do a first call for model initialization
            await self()
        # while True:
        async for r in self.model:
            yield r
            # await asyncio.sleep(1)  # wait a bit to fillup dataframe


async def ticker(pair: typing.Union[AssetPair, str], restclient: RestClient) -> Ticker:
    # async constructor, to enable RAII for this class when in async context.
    new_ticker = Ticker(pair=pair, restclient=restclient)
    # RAII()
    return await new_ticker()


if __name__ == '__main__':
    import time
    import asyncio
    from aiokraken.rest.client import RestClient
    from aiokraken.rest.api import Server
    from aiokraken.config import load_api_keyfile

    keystruct = load_api_keyfile()

    # Client can be global: there is only one.
    rest = RestClient(server=Server())

    # This creates the ledger for this asset
    tkr = Ticker(pair='XTZEUR', restclient=rest)

    # this retrieves (asynchronously and explicitely) the data

    async def consume():
        global tkr
        async for inf in tkr:
            print(inf)

    # The ticker loop needs to run, until consume is done
    #tkr.loop.run_until_complete(consume())
    tkr.loop.create_task(consume())
    tkr.loop.run_forever()

    # REMINDER : This must remain safe for the user : do not create any orders.
    # Rely on integration tests to validate any data processing.

