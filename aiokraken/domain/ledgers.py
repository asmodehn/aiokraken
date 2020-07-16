# TODO : self updating ledger...
import typing
from datetime import datetime, timedelta, timezone
import asyncio

from aiokraken.rest.schemas.kledger import KLedgerInfo
from bokeh.io import output_file, save

from aiokraken.domain.assets import Assets

from aiokraken.model.asset import Asset

from aiokraken.rest import RestClient

from aiokraken.model.ledgerframe import ledgerframe, LedgerFrame


class Ledger:
    """ Note : This is the monad / mutable state, providing an "imperative" interface to immutable data.
        There fore it should act as a container, on the (reversed) time axis...
    """
    model: LedgerFrame
    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??

    @classmethod
    async def retrieve(cls, start: datetime, end: datetime, rest: RestClient,
                       assets: typing.Optional[typing.List[typing.Union[Asset, str]]] = None,
                       loop = None):
        """ Retrieving all ledgers for a specific time period.
        Time is enforced to avoid long retrieval period. This can be relaxed when we have storage...
        Note this is intentionally somewhat orthogonal to construction of OHLC interface, based on assets... """
        # we retrieve all matching ledgerinfos...
        ledgerinfos, count = await rest.ledgers(start=start, end=end, asset=assets)

        # loop until we get *everything*
        # Note : if this is too much, leverage local storage (TODO ! - in relation with time... assume past data doesnt change)
        while len(ledgerinfos) < count:
            # Note : here we recurse only one time. we need to recurse to respect ratelimit...
            more_ledgers, count = await rest.ledgers(start=start, end=end, asset=assets, offset=len(ledgerinfos))
            ledgerinfos.update(more_ledgers)

        model = ledgerframe(ledger_as_dict=ledgerinfos).value

        return cls(ledgers=model, assets=assets, rest=rest, loop=loop)

    @property
    def begin(self):
        return self.model.begin

    @property
    def end(self):
        return self.model.end

    def __init__(self,  ledgers: LedgerFrame, rest: RestClient,
                 assets: typing.Optional[typing.List[typing.Union[Asset, str]]]=None,
                 loop = None):
        # We want just one asset at a time. Just like ohlc is one pair at a time.
        # Note ledger instances are mergeable vertically on this...

        self.restclient = rest if rest is not None else RestClient()

        self.loop = loop if loop is not None else asyncio.get_event_loop()   # TODO : use restclient loop ??

        self.model = ledgers
        self.assets = assets

    def query(self):
        # TODO : interface to query ledger request
        raise NotImplementedError

    async def __call__(self, start: datetime = None, stop: datetime = None,
                       assets: typing.Optional[typing.List[typing.Union[Asset, str]]] = None):
        """
        This is a call mutating this object after async rest data retrieval.
        """
        # self update
        # TODO : note how managing times here is similar to managing cache...
        #  probably in an another class, interfacing via decorator...

        if self.restclient is not None and (self.model is None or start < self.model.begin or stop > self.model.end):
            # we retrieve all matching ledgerinfos... lazy on times !
            ledgerinfos, count = await self.restclient.ledgers(asset=self.assets, start=start, end=stop, offset=0)

            # loop until we get *everything*
            # Note : if this is too much, leverage local storage (TODO ! - in relation with time... assume past data doesnt change)
            #  or refine filters (time, etc.)
            while len(ledgerinfos) < count:
                # Note : here we recurse only one time. we need to recurse to respect ratelimit...
                more_ledgers, count = await self.restclient.ledgers(asset=self.assets, start=start, end=stop, offset=len(ledgerinfos))
                ledgerinfos.update(more_ledgers)

            model = ledgerframe(ledger_as_dict=ledgerinfos)
            if model:
                self.model = model.value
            else:
                raise RuntimeError("Something went wrong")

        # we keep aggregating in place on the same object
        return self

    # TODO : maybe a property per asset and per ledger type, to avoid abusing getitem

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
                            stop=max(item.stop, self.end) if self.model else item.stop
                    ))
                    self.loop.run_until_complete(update_task)  # run the task in background and sync block.

                return Ledger(ledgers=self.model[item.start:item.stop], rest=self.restclient, assets=self.assets, loop=self.loop)

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

    async def retrieve_assets(assets):
        return await Assets.retrieve(assets=assets)

    al = asyncio.run(retrieve_assets(["EUR", "XBT", "XTZ"]))

    keystruct = load_api_keyfile()

    # Client can be global: there is only one.
    rest = RestClient(server=Server(key=keystruct.get('key'),
                                    secret=keystruct.get('secret')))

    async def retrieve_ledger(asset):
        return await Ledger.retrieve(asset=asset, rest=rest)

    for a in al:
        ldg = asyncio.run(retrieve_ledger(asset=a))

        # this retrieves (asynchronously and transparently) the data from the last week only
        now = datetime.now(tz=timezone.utc)
        for inf in ldg[now - timedelta(weeks=1): now]:
            print(inf)

        # f = ldg.layout()
        # output_file(f"{a}.html", mode='inline')
        # save(f)


    # REMINDER : This must remain safe for the user : do not create any orders.
    # Rely on integration tests to validate any data processing.

