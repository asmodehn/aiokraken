import typing
from datetime import timedelta, datetime

from aiokraken.rest.schemas.krequestorder import RequestOrder
from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken.model.assetpair import AssetPair

from aiokraken.model.ohlc import OHLC as OHLCModel
from aiokraken.rest import RestClient


class MarketData:
    """ This is a class gathering all data for a market.
    It relies on the AssetPair but also manages retrieval for a lot of related data.
    It is meant to be extended by the user to use as storage for all data you may want to gather on a market...

    It is most notably a mutable, often partially empty, instance.
    The main guarantee is that ohlc and indicators, signals, etc. are in sync.
    """

    updated: datetime  # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??
    validtime: timedelta  # The time between requests for market data (should be many seconds - more than rate limited REST API requirements)
    # TODO: websockets passive updating in background...

    pair: AssetPair
    tf_ohlc: typing.Dict[KTimeFrameModel, OHLCModel]  # this is a cache for previous requests (for any timeframe)
    # TODO : orderbook, etc. (cf kraken GUI for a market (trades, positions, etc.)
    #  Note : this is the model of what we will attempt to display in one local GUI...

    def __init__(self, pair: AssetPair, restclient: RestClient = None, valid_time: timedelta = None):
        self.restclient = restclient or RestClient()  # default restclient is possible here, but only usable for public requests...
        self.validtime = valid_time  # None means always valid
        self.pair = pair
        self.tf_ohlc = dict()

    async def __call__(self, timeframe: KTimeFrameModel = KTimeFrameModel.one_minute):
        """ Do the updates for this pair, at teh required timeframe """
        if timeframe not in self.tf_ohlc:  # creation on purpose... for now
            self.tf_ohlc[timeframe] = await ohlc(self.pair, timeframe=timeframe)

        else:  # just attempt an update (might await !)
            await self.tf_ohlc[timeframe]()

        # TODO : this should probably reschedule itself at a proper time...
        #   instead of expecting another call and awaiting

        return self  # returning mutated self for chaining api calls
    #
    # def __getitem__(self, item: KTimeFrameModel):
    #
    #     if not item in self.tf_ohlc:
    #
    #         return self.tf_ohlc[item]
    # TODO : how to do that ? async call from getitem ??

    # TODO : some user interactive confirmation, optional but by default...
    def market_sell(self, volume, execute=False, trade_future=False):
        # prepare the order
        order = RequestOrder(pair=self.pair.restname).market().sell(
            volume=volume).execute(execute)

        return self._pass_order(order=order, trade_future=trade_future)

    def market_buy(self, volume, execute=False, trade_future=False):
        # prepare the order
        order = RequestOrder(pair=self.pair.restname).market().buy(
            volume=volume).execute(execute)

        return self._pass_order(order=order, trade_future=trade_future)

    def limit_sell(self, limit_price, volume, execute=False, trade_future=False):
        # prepare the order
        order = RequestOrder(pair=self.pair.restname).limit(limit_price=limit_price).sell(
            volume=volume).execute(execute)

        return self._pass_order(order=order, trade_future=trade_future)

    def limit_buy(self, limit_price, volume, execute=False, trade_future=False):
        # prepare the order
        order = RequestOrder(pair=self.pair.restname).limit(limit_price=limit_price).buy(
            volume=volume).execute(execute)

        return self._pass_order(order=order, trade_future=trade_future)

    def stop_loss_sell(self, stop_loss_price, volume, execute= False, trade_future=False):

        # prepare the order
        order = RequestOrder(pair=self.pair.restname).stop_loss(stop_loss_price=stop_loss_price).sell(volume=volume).execute(execute)

        # pass the order
        return self._pass_order(order=order, trade_future=trade_future)

    def stop_loss_buy(self, stop_loss_price, volume, execute= False, trade_future=False):

        # prepare the order
        order = RequestOrder(pair=self.pair.restname).stop_loss(stop_loss_price=stop_loss_price).buy(volume=volume).execute(execute)

        # pass the order
        return self._pass_order(order=order, trade_future=trade_future)

    # TODO : representation of this is tricky...
    # We should have a main graph one, displaying it somehow...
    # On this graph we should be able to selectively display more or less data (ema or not, etc.)

    # TODO We should also be able to navigate the graph in various ways (time forward/back, timeframe + -, etc.)
    # Rule : only one window per market.


if __name__ == '__main__':
    import time
    import asyncio
    from aiokraken.rest.api import Server
    from aiokraken.markets import Markets
    from aiokraken.config import load_api_keyfile

    keystruct = load_api_keyfile()

    # Client can be global: there is only one.
    priv_client = RestClient(server=Server(
        #key=keystruct.get('key'),
        #secret=keystruct.get('secret')
    ))
    # priv client is needed since we get orders and trades...
    # TODO : maybe split into another class ??

    mkts = Markets(restclient=priv_client)

    async def assetpairs_retrieve_nosession():
        await mkts()
        for k, p in mkts.items():
            print(f" - {k}: {p}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(assetpairs_retrieve_nosession())
    time.sleep(1)

    # market data can be global (one per market only)
    # TODO : type for market to avoid identifier mistakes (altname, etc.)
    md = MarketData(pair=mkts.details.get('XETHZEUR'), restclient=priv_client)

    async def ohlc_retrieve_nosession():
        await md()

    # TODO : better to have rest client in object or in call ??

    loop.run_until_complete(ohlc_retrieve_nosession())
    ohlc = md.tf_ohlc.get(KTimeFrameModel.one_minute)
    print(f"from: {ohlc.begin} to: {ohlc.end} -> {len(ohlc)} values")
    assert len(ohlc) == 720

    print("Waiting one more minute to attempt retrieving more ohlc data and stitch them...")
    time.sleep(60)
    loop.run_until_complete(ohlc_retrieve_nosession())
    # Note : OHLC has been modified in background, we dont need to change the reference we already got.
    print( f"from: {ohlc.begin} to: {ohlc.end} -> {len(ohlc)} values")
    assert len(ohlc) == 721

    loop.close()

