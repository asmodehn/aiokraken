import asyncio

import typing
from datetime import datetime

from result import Result

from aiokraken.model.tradehistory import TradeHistory, trade_history
from timecontrol.overlimiter import OverLimiter
from timecontrol.command import Command

from aiokraken.assets import Assets
from aiokraken.markets import Markets

from aiokraken import RestClient
from aiokraken.model.ledger import Ledger, ledger
from aiokraken.model.assetpair import AssetPair
from aiokraken.model.time import Time
from aiokraken.rest import Server
from aiokraken.utils.filter import Filter




class Client:
    """
    A client class to regroup REST and WS protocols to interract with the exchange.
    Also batching REST requests to optimize them...
    Basically a container for requests and subscriptions...
    """

    def __init__(self, key =None, secret=None):
        # Note : we get a client for public requests only if the key/secret is not passed
        # Otherwise, we get a private client that we use for everything
        # => private/public distinction handled in .rest.client
        self.rest = RestClient(server=Server(key=key, secret=secret))

        # self.wss = WssClient()  # TODO

    async def __call__(self):
        """ schedule rest calls and ws subscriptions to optimize time..."""
        async with self.rest as rest:
            # grouping requests execution
            pass
            # Full refresh of global, time-UNrelated, data
            # TODO : review these models...
            # self.time = await rest.time()()
            # TODO get a model of time, potentially solving clock misalignement, etc.

            # self.assets = Assets(await rest.assets()())  # TODO : something for this useless double call

            # self.markets = Markets(await rest.assetpairs()())
            # Ticker... attribute of market ?

    # TODO: "requests" of time-related data, returning dataframes.
    # async def trades:
    #   raise NotImplementedError
    #
    # async def ohlc(pair):
    #   raise NotImplementedError
    #
    # async def orders(pair):
    #   raise NotImplementedError



    # TODO : at this level, we can manage a cache (result dataframe in db, or so)
    async def ledger(self, start: datetime = None, end: datetime = None) -> Result[Ledger, Exception]:
        # TODO : at this level we manage the time of the request
        """ request ledger from kraken """

        ledgerinfos, count = await self.rest.ledgers(offset=0, start=start, end=end)()

        # loop until we get *everything*
        # Note : if this is too much, leverage local storage (TODO ! - in relation with time... assume past data doesnt change)
        #  or refine filters (time, etc.)
        while len(ledgerinfos) < count:
            # Note : here we recurse only one time. we need to recurse to respect ratelimit...
            more_ledgers, count = await self.rest.ledgers(offset=len(ledgerinfos), start=start, end=end)()
            ledgerinfos.update(more_ledgers)

        # TODO : here we should probably convert to a Model (dataframe, etc.),
        # more complex/complete than a dict structure...

        ldgr = ledger(ledger_as_dict=ledgerinfos)
        # REMINDER : imperative / immutable (from user point of view) semantics.
        return ldgr

    # TODO : at this level, we can manage a cache (result dataframe in db, or so)
    async def tradehistory(self, start: datetime = None, end: datetime = None) -> Result[TradeHistory, Exception]:
        # TODO : at this level we manage the time of the request
        """ request ledger from kraken """

        trades, count = await self.rest.trades(offset=0, start=start, end=end)()

        # loop until we get *everything*
        # Note : if this is too much, leverage local storage (TODO ! - in relation with time... assume past data doesnt change)
        #  or refine filters (time, etc.)
        while len(trades) < count:
            # Note : here we recurse only one time. we need to recurse to respect ratelimit...
            more_trades, count = await self.rest.trades(offset=len(trades), start=start, end=end)()
            trades.update(more_trades)

        # TODO : here we should probably convert to a Model (dataframe, etc.),
        # more complex/complete than a dict structure...

        trdh = trade_history(tradehistory_as_dict=trades)
        # REMINDER : imperative / immutable (from user point of view) semantics.
        return trdh


    #
    # async def __aenter__(self): TODO : maybe this just calls itself ?
    #     # Opens client Session (cannot be done in init or in module import)
    #     await self.rest.__aenter__()
    #     try:
    #         # initializes everything async (cannot be done in init or in module import)
    #
    #         # Note : assets affect balance considered, markets affect markets considered (TODO)
    #         # M market and A asset might not be related at all ? cf. with leverage I can trade anything ??
    #         # Or maybe there is a rule, like a market must have at least one asset as part of the pair ?
    #
    #         # Goal: provide Guarantees : we can spend only assets in only markets.
    #         return self
    #
    #     except Exception as e:
    #         LOGGER.error(e, exc_info=True)
    #         raise  # Let someone else reset me...
    #
    # async def __aexit__(self, exc_type, exc_val, exc_tb):
    #     await self.rest.__aexit__(exc_type=exc_type, exc_val=exc_val, exc_tb=exc_tb)

if __name__ == '__main__':
    import time
    import asyncio
    from aiokraken.rest.client import RestClient, RestClient, RestClient
    from aiokraken.rest.api import Server
    from aiokraken.config import load_api_keyfile

    keystruct = load_api_keyfile()

    # Client can be global: there is only one.
    client = Client(key=keystruct.get('key'), secret=keystruct.get('secret'))

    async def client_run():
        global client
        # TODO
        # await client()  # client initialization (retrieve basic general data)
        # print(client.time)
        # for k, v in client.assets.items():
        #     print(f" - {k}: {v}")
        # for k, v in client.markets.items():
        #     print(f" - {k}: {v}")

        # async for to iterate on timeindexed rows (and optionally retrieve recent ones !)...
        L = await client.ledger()
        if L:
            for r in L.value:
                print(f" - {r}")
        else:
            print(f"There was an error with {L}")

        # async for to iterate on timeindexed rows (and optionally retrieve recent ones !)...
        TH = await client.tradehistory()
        if TH:
            for r in TH.value:
                print(f" - {r}")
        else:
            print(f"There was an error with {TH}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(client_run())

    # REMINDER : This must remain safe for the user : do not create any orders.
    # Rely on integration tests to validate merging of data.

    loop.close()