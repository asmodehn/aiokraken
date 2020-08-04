""" Module to represent the market interaction onto the user. This is hte dual of Order.

These are the private user's trades. It is closely related to the user ledger...
"""
import asyncio
import typing
from datetime import datetime
from types import MappingProxyType

from aiokraken.websockets.privateapi import ownTrades

from aiokraken.config import load_api_keyfile
from aiokraken.assetpairs import AssetPairs

from aiokraken.model.tradeframe import TradeFrame, tradeframe

from aiokraken.rest import RestClient, Server


class Trades:
    """
    Trade *history* of the user.
    This is also where all analysis function about past trading performance should be available...
    """
    @classmethod
    async def retrieve(cls, rest: RestClient = None, start: datetime =None, end: datetime = None, loop=None):
        rest = RestClient() if rest is None else rest

        trades, count = await rest.trades(start=start, end=end)

        # loop until we get *everything*
        # Note : if this is too much, leverage local storage (TODO ! - in relation with time... assume past data doesnt change)
        while len(trades) < count:
            # Note : here we recurse only one time. we need to recurse to respect ratelimit...
            more_trades, count = await rest.trades(start=start, end=end, offset=len(trades))
            trades.update(more_trades)

        model = tradeframe(tradehistory_as_dict=trades).value

        return cls(trades=model, rest=rest, loop=loop)

    model: TradeFrame

    @property
    def begin(self):
        return self.model.begin

    @property
    def end(self):
        return self.model.end

    def __init__(self, trades: TradeFrame, rest: RestClient, loop = None):

        self.rest = rest if rest is not None else RestClient()

        self.loop = loop if loop is not None else asyncio.get_event_loop()   # TODO : use restclient loop ??

        self.model = trades

    # TODO : somehow keep this to express the dual of "adding order to the exchange"
    async def __call__(self, start: datetime=None, end: datetime=None):

        if self.rest is not None and (self.model is None or start < self.model.begin or end > self.model.end):
            # we retrieve all matching ledgerinfos... lazy on times !
            trades, count= await rest.trades(start=start, end=end)

            # loop until we get *everything*
            # Note : if this is too much, leverage local storage (TODO ! - in relation with time... assume past data doesnt change)
            while len(trades) < count:
                # Note : here we recurse only one time. we need to recurse to respect ratelimit...
                more_trades, count = await rest.trades(start=start, end=end, offset=len(trades))
                trades.update(more_trades)

            model = tradeframe(tradehistory_as_dict=trades)
            if model:
                self.model = model.value
            else:
                raise RuntimeError("Something went wrong")

        # we keep aggregating in place on the same object
        return self

    def __getitem__(self, item):
        # TODO : also access with txid !!
        if isinstance(item, datetime):
            return self.model[item]
        elif isinstance(item, slice):
            # if the model is empty, just return self instead of excepting.
            if not self.model:
                return self
            # check for slice of times
            if isinstance(item.start, datetime) and isinstance(item.stop, datetime):
                # Retrieve data if needed and block (sync)
                if self.model is None or item.start < self.begin or item.stop > self.end:
                    update_task = self.loop.create_task(
                        self(  # TODO : stitching to be managed like a cache (decorator around __call__)
                            start=min(item.start, self.begin) if self.model else item.start,
                            end=max(item.stop, self.end) if self.model else item.stop
                    ))
                    self.loop.run_until_complete(update_task)  # run the task in background and sync block.

                return Trades(trades=self.model[item.start:item.stop], rest=self.rest, loop=self.loop)

        else:  # anything else : rely on the model
            # TODO : also access per asset or asset list - container-style
            return self.model[item]

    def __contains__(self, item):
        if isinstance(item, datetime):
            return item in self.model
        else:
            raise NotImplementedError

    def __iter__(self):
        """ directly delegate to time-based iteration on the inner model """
        return self.model.__iter__()

    async def __aiter__(self):
        # this is were we leverage our websocket implementation
        # forwarding every update to the user (and also using it internally to update the model,
        # waiting for the next (user-triggered) rest request...

        # Using minimal timeframe of all for this update
        async for trades_update in ownTrades(restclient=self.rest):
            # TODO : decides if this update means the previous one is final (we cannot do better until we synchronize client and server time...)
            # TODO : store this update until next iteration
            # TODO : update internal model

            yield trades_update

    def __len__(self):
        if self.model is not None:
            return len(self.model)
        else:
            return 0


if __name__ == '__main__':

    import time
    import asyncio
    from aiokraken.rest.client import RestClient, RestClient, RestClient
    from aiokraken.rest.api import Server
    from aiokraken.config import load_api_keyfile
    from datetime import timedelta, timezone, datetime

    # late client (private session) initialization
    keystruct = load_api_keyfile()

    # Client can be global: there is only one.
    rest = RestClient(server=Server(key=keystruct.get('key'),
                                    secret=keystruct.get('secret')))

    async def retrieve_trades():
        return await Trades.retrieve(rest=rest)

    tdh = asyncio.run(retrieve_trades())

    # this retrieves (asynchronously and transparently) the data from the last week only
    now = datetime.now(tz=timezone.utc)
    for inf in tdh[now - timedelta(weeks=1): now]:
        print(inf)

        # f = ldg.layout()
        # output_file(f"{a}.html", mode='inline')
        # save(f)

    # REMINDER : This must remain safe for the user : do not create any orders.
    # Rely on integration tests to validate any data processing.

