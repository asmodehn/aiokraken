# TODO : self updating ledger...
import typing
from datetime import datetime, timedelta, timezone
from types import MappingProxyType

from aiokraken.model.asset import Asset

from aiokraken.rest import RestClient

from aiokraken.model.ledgerframe import ledgerframe, LedgerFrame


class Ledger:
    """ Note : This is the monad / mutable state, providing an "imperative" interface to immutable data.
        There fore it should act as a container, on the (reversed) time axis...
    """
    model: LedgerFrame
    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??

    @property
    def begin(self):
        return self.model.begin

    @property
    def end(self):
        return self.model.end

    def __init__(self,  restclient: RestClient, asset: typing.Union[Asset, str], loop = None):
        self.asset = asset  # TODO: None asset is "all" (API default)
        self.restclient = restclient
        # Note if Restclient is None, this is just a proxy,
        # it cannot update by itself, it doesnt really "contain" data.

        self.loop = loop if loop is not None else asyncio.get_running_loop()
        self.model = None  # Need async call : raii is not doable here...
        # TODO : mapping proxy to avoid mutation problems ?

    async def __call__(self, start: datetime = None, stop: datetime = None):  # TODO : pass necessary parameters (cf ledger request)
        # self update
        # TODO : note how managing times here is similar to managing cache... probably in an another class, interfacing via decorator...

        if self.restclient is not None and (self.model is None or start < self.model.begin or stop > self.model.end):
            # we retrieve all matching trades... lazy on times !
            ledgerinfos, count = await self.restclient.ledgers(asset=self.asset, start=start, end=stop, offset=0)

            # loop until we get *everything*
            # Note : if this is too much, leverage local storage (TODO ! - in relation with time... assume past data doesnt change)
            #  or refine filters (time, etc.)
            while len(ledgerinfos) < count:
                # Note : here we recurse only one time. we need to recurse to respect ratelimit...
                more_ledgers, count = await self.restclient.ledgers(asset=self.asset,start=start, end=stop, offset=len(ledgerinfos))
                ledgerinfos.update(more_ledgers)

            # TODO : here we should probably convert to a Model (dataframe, etc.),
            # more complex/complete than a dict structure...

            model = ledgerframe(ledger_as_dict=ledgerinfos)
            if model:
                self.model = model.value
            else:
                raise RuntimeError("Something went wrong")

        # ELSE if there is no client, it means this instance is supposed to be just a proxy on the mutating data.
        # OR WE want to make a specific class ??? Probably AFTER doing the timeindexed dataframe for trades.

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

# TODO : different kind of ledger (from client.py)
# ledger as a slice in time (directed container), with "request by need" of the appropriate timeframe.
# also provide mapping interface, " per asset " or " per type " of the current ledger slice


async def ledger(asset: typing.Union[Asset, str], restclient: RestClient, begin: datetime = None, end: datetime = None) -> Ledger:
    # async constructor, to enable RAII for this class when in async context.
    new_ledger = Ledger(asset=asset, restclient=restclient)
    # RAII()
    return await new_ledger(start=begin, stop=end)


if __name__ == '__main__':
    import time
    import asyncio
    from aiokraken.rest.client import RestClient, RestClient, RestClient
    from aiokraken.rest.api import Server
    from aiokraken.config import load_api_keyfile

    keystruct = load_api_keyfile()

    # Client can be global: there is only one.
    rest = RestClient(server=Server(key=keystruct.get('key'),
                                    secret=keystruct.get('secret')))

    loop = asyncio.get_event_loop()  # get or create the event loop

    # This creates the ledger for this asset
    ldg = Ledger(asset='XTZ', restclient=rest, loop=loop)

    # this retrieves (asynchronously and transparently) the data from the last week only
    now = datetime.now(tz=timezone.utc)
    for inf in ldg[now - timedelta(weeks=1): now]:
        print(inf)

    # REMINDER : This must remain safe for the user : do not create any orders.
    # Rely on integration tests to validate any data processing.

