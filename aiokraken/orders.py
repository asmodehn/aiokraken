""" Module to represent the user interaction onto the market. This is the dual of Trades.

These are the private user's Orders
"""
import asyncio
import typing
from datetime import datetime, timedelta, timezone
from types import MappingProxyType

from aiokraken.websockets.privateapi import openOrders

from aiokraken.model.assetpair import AssetPair

from aiokraken.config import load_api_keyfile
from aiokraken.model.orderframe import OrderFrame, closedorderframe, openorderframe

from aiokraken.rest.schemas.kclosedorder import KClosedOrderModel

from aiokraken.rest import RestClient, Server
from aiokraken.rest.schemas.kopenorder import KOpenOrderModel


class Orders:
    """
    """
    @classmethod
    async def retrieve(cls, rest: RestClient = None, start: datetime =None, end: datetime = None, loop=None):
        rest = RestClient() if rest is None else rest

        corders, count = await rest.closedorders(start=start, end=end)

        # loop until we get *everything*
        # Note : if this is too much, leverage local storage (TODO ! - in relation with time... assume past data doesnt change)
        while len(corders) < count:
            # Note : here we recurse only one time. we need to recurse to respect ratelimit...
            more_corders, count = await rest.closedorders(start=start, end=end, offset=len(corders))
            corders.update(more_corders)

        cmodel = closedorderframe(closedorders_as_dict=corders).value

        # ALso retrieving currently open orders

        oorders = await rest.openorders()

        omodel = openorderframe(openorders_as_dict=oorders).value

        return cls(closedorders=cmodel, openorders=omodel, rest=rest, loop=loop)

    closed: OrderFrame
    open: OrderFrame

    @property
    def begin(self):
        return self.closed.begin

    @property
    def end(self):
        return self.closed.end

    def __init__(self, closedorders: OrderFrame, openorders: OrderFrame, rest: RestClient, loop = None):

        self.rest = rest if rest is not None else RestClient()

        self.loop = loop if loop is not None else asyncio.get_event_loop()   # TODO : use restclient loop ??

        self.closed = closedorders
        self.open = openorders

        # TODO : we should probably filter/index by assets (related, in- or out-going)
        #  This has to be the dual of trades, which is filtered/indexed on pairs.

    @classmethod
    def market(self):
        """ a method to pass a market order ??? """
        raise NotImplementedError
        return # TODO via REST

    @property
    def limit(self):
        """ a method to pass a limit order ??? """
        raise NotImplementedError
        return # TODO via REST


    async def __call__(self, start: datetime=None, end: datetime=None):

        if self.rest is not None and (self.model is None or start < self.model.begin or end > self.model.end):
            # we retrieve all matching ledgerinfos... lazy on times !
            closedorders, count= await rest.closedorders(start=start, end=end)

            # loop until we get *everything*
            # Note : if this is too much, leverage local storage (TODO ! - in relation with time... assume past data doesnt change)
            while len(closedorders) < count:
                # Note : here we recurse only one time. we need to recurse to respect ratelimit...
                more_orders, count = await rest.closedorders(start=start, end=end, offset=len(closedorders))
                closedorders.update(more_orders)

            model = closedorderframe(closedorders_as_dict=closedorders)
            if model:
                self.model = model.value
            else:
                raise RuntimeError("Something went wrong")

            # ALso update open orders, replacing older content
            oorders = await rest.openorders()

            self.open = openorderframe(openorders_as_dict=oorders).value
        # we keep aggregating in place on the same object
        return self

    def __getitem__(self, item):
        # TODO : also access with txid !!
        if isinstance(item, datetime):
            return self.closed[item]  # TODO : what about open orders ?
        elif isinstance(item, slice):
            # if the model is empty, just return self instead of excepting.
            if not self.closed:
                return self
            # check for slice of times
            if isinstance(item.start, datetime) and isinstance(item.stop, datetime):
                # Retrieve data if needed and block (sync)
                if self.closed is None or item.start < self.begin or item.stop > self.end:
                    if not self.loop.is_closed():
                        update_task = self.loop.create_task(
                            self(  # TODO : stitching to be managed like a cache (decorator around __call__)
                                start=min(item.start, self.begin) if self.closed else item.start,
                                end=max(item.stop, self.end) if self.closed else item.stop
                        ))
                        self.loop.run_until_complete(update_task)  # run the task in background and sync block.
                return Orders(closedorders=self.closed[item.start:item.stop], openorders=self.open, rest=self.rest, loop=self.loop)

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
        return self.closed.__iter__()  # Only iterate through closed orders implicitely.
        # open ones are available via the async iterator

    async def __aiter__(self):
        # this is were we leverage our websocket implementation
        # forwarding every update to the user (and also using it internally to update the model,
        # waiting for the next (user-triggered) rest request...

        # Using minimal timeframe of all for this update
        async for orders_update in openOrders(restclient=self.rest):
            # TODO : decides if this update means the previous one is final (we cannot do better until we synchronize client and server time...)
            # TODO : store this update until next iteration
            # TODO : update internal model

            # Note : we should here return the currently opened orders to the user (following the lookahead in time perspective)
            # detect opened AND closed orders and update both model.
            yield orders_update

    def __len__(self):
        if self.model is not None:
            return len(self.model)
        else:
            return 0


if __name__ == '__main__':

    # late client (private session) initialization
    keystruct = load_api_keyfile()

    # Client can be global: there is only one.
    rest = RestClient(server=Server(key=keystruct.get('key'),
                                    secret=keystruct.get('secret')))

    async def retrieve_orders():
        return await Orders.retrieve(rest=rest)

    orders = asyncio.run(retrieve_orders())

    # this retrieves (asynchronously and transparently) the data from the last week only
    now = datetime.now(tz=timezone.utc)
    for inf in orders[now - timedelta(weeks=1): now]:
        print(inf)

        # f = ldg.layout()
        # output_file(f"{a}.html", mode='inline')
        # save(f)

    # REMINDER : This must remain safe for the user : do not create any orders.
    # Rely on integration tests to validate any data processing.


