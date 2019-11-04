import time
from decimal import Decimal, localcontext, DefaultContext

import aiohttp
import asyncio
import signal

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from aiokraken.rest.client import RestClient

from aiokraken.rest.schemas.krequestorder import RequestOrder
from aiokraken.rest.schemas.kopenorder import KOpenOrderModel
from aiokraken.rest.schemas.korderdescr import KOrderDescrOnePrice, KOrderDescr

LOGGER = get_kraken_logger(__name__)


# Stupid bot

async def get_time():
    """ get kraken time"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.time()
        print(f'response is {response}')
    finally:
        await rest_kraken.close()


@asyncio.coroutine
def ask_exit(sig_name):
    print("got signal %s: exit" % sig_name)
    yield from asyncio.sleep(1.0)
    asyncio.get_event_loop().stop()


class Proxy:
    """
    Proxy class to only do request when needed... careful with calling rates.
    # TODO : integrate this in library API...
    """

    def __init__(self,rest_client,):
        self.rest_client = rest_client
        # TODO : integrate with API and  maybe have some basic control algo ?
        self.public_period_limit = 1  # secs
        self.private_period_limit = 10 # secs

        self._last_public_call = time.time()
        self._last_ticker = None
        self._last_ohlcv = None
        self._last_assets = None
        self._last_assetpairs = None

        self._last_private_call = time.time()
        self._last_balance = None
        LOGGER.info(f"Proxy created. time: {int(time.time())}")

    async def assets(self, assets=None, wait_for_it = False):
        now = time.time()
        # CAREFUL with timer, we cannot limit restart of software !
        # Better to start slowly, just in case...

        epsilon = 1  # needed to workaround innaccurate time measurements on sleep (depend on OS...)
        if self._last_assets is None or (wait_for_it and now - self._last_public_call < self.public_period_limit):
            await asyncio.sleep(self.public_period_limit - now + self._last_public_call + epsilon)
            now = time.time()
        if self._last_assets is None or now - self._last_public_call > self.public_period_limit:
            self._last_public_call = now
            self._last_assets = await self.rest_client.assets(assets=assets)
            LOGGER.info(f"Assets: {self._last_assets}")

        res = self._last_assets
        return res

    async def assetpairs(self, assets=None, wait_for_it = False):
        now = time.time()
        # CAREFUL with timer, we cannot limit restart of software !
        # Better to start slowly, just in case...

        epsilon = 1  # needed to workaround innaccurate time measurements on sleep (depend on OS...)
        if self._last_assetpairs is None or (wait_for_it and now - self._last_public_call < self.public_period_limit):
            await asyncio.sleep(self.public_period_limit - now + self._last_public_call + epsilon)
            now = time.time()
        if self._last_assetpairs is None or now - self._last_public_call > self.public_period_limit:
            self._last_public_call = now
            self._last_assetpairs = await self.rest_client.assetpairs(assets=assets)
            LOGGER.info(f"AssetPairs: {self._last_assetpairs}")

        res = self._last_assetpairs
        return res

    async def ticker(self, pairs=None, wait_for_it = False):
        now = time.time()
        # CAREFUL with timer, we cannot limit restart of software !
        # Better to start slowly, just in case...

        epsilon = 1  # needed to workaround innaccurate time measurements on sleep (depend on OS...)
        if self._last_ticker is None or (wait_for_it and now - self._last_public_call < self.public_period_limit):
            await asyncio.sleep(self.public_period_limit - now + self._last_public_call + epsilon)
            now = time.time()
        if self._last_ticker is None or now - self._last_public_call > self.public_period_limit:
            self._last_public_call = now
            self._last_ticker = await self.rest_client.ticker(pairs=pairs)  # TODO :FIXIT to pass the pair...
            LOGGER.info(f"Ticker for {pairs}: {self._last_ticker}")

        res = self._last_ticker
        return res

    async def ohlcv(self, pair, wait_for_it = False):
        now = time.time()
        # CAREFUL with timer, we cannot limit restart of software !
        # Better to start slowly, just in case...

        epsilon = 1  # needed to workaround innaccurate time measurements on sleep (depend on OS...)
        if self._last_ohlcv is None or (wait_for_it and now - self._last_public_call < self.public_period_limit):
            await asyncio.sleep(self.public_period_limit - now + self._last_public_call + epsilon)
            now = time.time()
        if self._last_ohlcv is None or now - self._last_public_call > self.public_period_limit:
            self._last_public_call = now
            self._last_ohlcv = await self.rest_client.ohlc(pair=pair)
            LOGGER.debug(f"OHLCV for {pair} : {self._last_ohlcv}")

        res = self._last_ohlcv
        return res

    async def balance(self, wait_for_it = False):  # Note : the wait_for_it is not about public/private, but about GET/POST behavior...
        now = time.time()

        epsilon = 1  # needed to workaround innaccurate time measurements on sleep (depend on OS...)
        if self._last_balance is None or (wait_for_it and now - self._last_private_call < self.private_period_limit):
            await asyncio.sleep(self.private_period_limit - now + self._last_private_call + epsilon)
            now = time.time()
        if self._last_balance is None or now - self._last_private_call > self.private_period_limit:
            self._last_private_call = now
            self._last_balance = await self.rest_client.balance()
            LOGGER.info(f"Balance API called : {self._last_balance}")

        res = self._last_balance
        return res

    async def addorder(self, order):
        """

        :param order:
        :return: txid
        """
        now = time.time()
        epsilon = 1  # needed to workaround innaccurate time measurements on sleep (depend on OS...)
        if now - self._last_private_call < self.private_period_limit:
            await asyncio.sleep(self.private_period_limit - now + self._last_private_call + epsilon)
            now = time.time()
        if now - self._last_private_call > self.private_period_limit:
            self._last_private_call = now
            response = await self.rest_client.addorder(order=order)
            LOGGER.info(f"AddOrder API called with {order}")
            LOGGER.info(f"-> {response}")
            # self_orders.append = res  # TODO : order manager
            return response
        return None  # Note: proxying response here does not make any sense

    async def openorders(self):
        """

        :param order:
        :return: txid
        """
        now = time.time()
        epsilon = 1  # needed to workaround innaccurate time measurements on sleep (depend on OS...)
        if now - self._last_private_call < self.private_period_limit:
            await asyncio.sleep(self.private_period_limit - now + self._last_private_call + epsilon)
            now = time.time()
        if now - self._last_private_call > self.private_period_limit:
            self._last_private_call = now
            response = await self.rest_client.openorders()
            LOGGER.info(f"OpenOrder API called")
            LOGGER.info(f"-> {response}")
            # self_orders.append = res  # TODO : order manager
            return response
        return None  # Note: proxying response here does not make any sense

    async def cancel(self, txid):
        res = None
        now = time.time()
        epsilon = 1  # needed to workaround innaccurate time measurements on sleep (depend on OS...)
        if now - self._last_private_call < self.private_period_limit:
            await asyncio.sleep(self.private_period_limit - now + self._last_private_call + epsilon)
            now = time.time()
        if now - self._last_private_call > self.private_period_limit:
            self._last_private_call = now
            response = await self.rest_client.cancel(txid=txid)
            LOGGER.info(f"Cancel API called with {txid}")
            LOGGER.info(f"-> {response}")
            return response
        return None  # Note: proxying response here does not make any sense


# TODO : related to the command design pattern?
class OrderEnterBullishStrategy:
    """
    Elementary strategy
    # TODO : start with very broadly accepting trigger (ex: RSI 40) from indicators (it helps testing actions triggered)
    #  and then tune them, step by step...
    """

    def __init__(self, rest_client_proxy, pair, pairinfo):
        self.rest_client_proxy = rest_client_proxy
        self.pair = pair
        self.pairinfo = pairinfo

    async def __call__(self, volume, callonexit, execute = False):
        # correct volume
        volume = round(volume, self.pairinfo.lot_decimals)

        # wait for the right moment

        ohlc = await self.rest_client_proxy.ohlcv(pair=self.pair)
        while isinstance(ohlc, dict):
            # TODO : check for error 5XX before retry
            await asyncio.sleep(3)
            ohlc = await self.rest_client_proxy.ohlcv(pair=self.pair)
        ohlc.rsi()
        rsi = ohlc.dataframe[['time', 'close', 'RSI_14']]  # getting last RSI value. We also need to keep close price around...

        # making sure the time of the measure
        assert int(time.time()) - rsi.iloc[-1]['time'] < 100  # expected timeframe of 1 minutes by default  # TODO : manage TIME !!!

        if rsi.iloc[-1]['RSI_14'] > 65:  # TODO : combine MACD and RSI as trade signal... ?
            except_count = 0
            LOGGER.debug(f"RSI: \n{rsi}.")
            LOGGER.info(f"RSI: {rsi.iloc[-1]['RSI_14']} Commencing Bullish strategy...")
            ticker = (await self.rest_client_proxy.ticker(pairs=[self.pair]))[self.pairinfo.base + self.pairinfo.quote]  #TODO : find better way to handle both names...

            # extract current price as midpoint of bid and ask from ticker
            price = round((ticker.ask.price + ticker.bid.price) / 2, self.pairinfo.pair_decimals)
            #limit_price = round(price * Decimal(1.010))
            # low limit price to have high probability to hit this before hitting stop loss ?
            # but high enough to get enough time to reframe the trade ?

            # deducting stop_loss price from last time RSI passed 50:
            upward_close_price = price  # first approximation
            for i, r in rsi.iloc[::-1].iterrows():  # or itertuples, depending...
                if r['RSI_14'] < 50:
                    upward_close_price = r['close']
                    break

            stop_loss_price = round(upward_close_price, self.pairinfo.pair_decimals)

            #trailing_stop_offset = round(price * Decimal(-0.0026), self.pairinfo.pair_decimals)
            # because fees ? TODO : base this on derivative of RSI, as a predictor of likelyhood of not hitting it ?

            # LOGGER.info(f"Price for {self.pair}: {price}. Passing Enter Order with trailing stop at {trailing_stop_offset}")
            LOGGER.info(f"Price for {self.pair}: {price}. Passing Enter Order with stop loss at {stop_loss_price}")
            # bull trend
            try:
                mo = await self.rest_client_proxy.addorder(RequestOrder(pair=self.pair).market().bid(volume=volume, # close=KOrderDescr(pair=self.pair)
                                                                                                     #.trailing_stop(trailing_stop_offset=trailing_stop_offset))
                                                           ).execute(execute))
                slo = await self.rest_client_proxy.addorder(RequestOrder(pair=self.pair).stop_loss(stop_loss_price=stop_loss_price).sell(volume=volume).execute(execute))
                #ts = await self.rest_client_proxy.addorder(RequestOrder(pair=self.pair).trailing_stop(trailing_stop_offset=trailing_stop_offset).ask(volume=volume).execute(execute))
                # TODO : trailing stop probably better here ? as close order ?
                #   Currently : {'error': ['EGeneral:Invalid arguments:ordertype']}

                if execute:  # We should get transaction ID, so we can track the open orders...
                    print(f"MarketOrder returned : {mo}")
                    print(f"Stop Loss returned : {slo}")
                    #print(f"Trailing stop returned : {ts}")
                    txid = mo.get('txid')[0]  # only one stop loss order passed by the order request
                    # TODO : we should go to exit strat only after market order is fullfilled.
                    #   This is a profit optimisation on the trailing stop...
                    oo = await self.rest_client_proxy.openorders()
                    print(oo)  # NOTE : We need execute = True to get anything here...

                    while txid in oo:
                        oo = await self.rest_client_proxy.openorders()
                        print(oo)  # NOTE : We need execute = True to get anything here...

                    print(f'{txid} has been filled !')

                # trigger exit strat
                LOGGER.info(f"Triggering Bull Exit watch...")
                return asyncio.create_task(callonexit(volume=volume, execute=execute, enter_price=price, stop_loss_order=slo.get('txid')[0]))  # only one stop loss order

                # exit and die.
            except Exception as e:
                except_count +=1
                LOGGER.error(f"Exception caught : {e}.", exc_info=True)
                # TODO :FIX this : need to be passed to recursive call
                # if except_count < 3:
                #     LOGGER.warning(f"Retrying...")
                # else:
                raise
        else:
            LOGGER.debug(f"RSI: \n{rsi}")
            LOGGER.info(f"RSI: {rsi.iloc[-1]['RSI_14']} sleeping for a bit...")
            await asyncio.sleep(10)
            # looping...
            return asyncio.create_task(self(volume=volume, callonexit=callonexit, execute=execute))


class OrderExitBullishStrategy:
    """
    Elementary strategy
    """

    def __init__(self, rest_client_proxy, pair, pairinfo):
        self.rest_client_proxy = rest_client_proxy
        self.pair = pair
        self.pairinfo = pairinfo

    # TODO : design review : same volume, 'exit' behavior could retrigger 'enter' behavior...
    #  and we wouldnt need a supervisor...
    async def __call__(self, volume, enter_price, stop_loss_order=None, execute=False):
        # correct volume
        volume = round(volume, self.pairinfo.lot_decimals)

        # wait for the right moment

        ohlc = await self.rest_client_proxy.ohlcv(pair=self.pair)
        while isinstance(ohlc, dict):
            # TODO : check for error 5XX before retry
            await asyncio.sleep(3)
            ohlc = await self.rest_client_proxy.ohlcv(pair=self.pair)

        ohlc.rsi()
        rsi = ohlc.dataframe[['time', 'RSI_14']]  # getting last RSI value

        # making sure the time of the measure
        assert int(time.time()) - rsi.iloc[-1]['time'] < 100  # expected timeframe of 1 minutes by default  # TODO : manage TIME !!!

        ticker = (await self.rest_client_proxy.ticker(pairs=[self.pair]))[
            self.pairinfo.base + self.pairinfo.quote]  # TODO : find better way to handle both names...
        # extract current price as midpoint of bid and ask from ticker
        price = round((ticker.ask.price + ticker.bid.price) / 2, self.pairinfo.pair_decimals)

        if rsi.iloc[-1]['RSI_14'] < 50:
            # Seems we should not exit too quickly (<65), if we want to be albe to profit fron longer trends...
            # Note that in case of emergency the stop loss should kick in and get us out of the position.
            except_count = 0
            LOGGER.debug(f"RSI: \n{rsi}")
            LOGGER.info(f"RSI: {rsi.iloc[-1]['RSI_14']} Terminating Bullish strategy...")

            #stop_loss_price = round(price * Decimal(1.05), self.pairinfo.pair_decimals)

            LOGGER.info(f"Price for {self.pair}: {price}. Passing Exit Order ")  #with stop loss at {stop_loss_price}")
            # Not bull any longer : pass the inverse/complementary order...
            try:
                mo = await self.rest_client_proxy.addorder(RequestOrder(pair=self.pair).market().sell(volume=volume).execute(execute))
                #slo = await self.rest_client_proxy.addorder(RequestOrder(pair=self.pair).stop_loss(stop_loss_price=stop_loss_price).buy(volume=volume))
                # TODO : trailing stop probably better here ? as close order ?

                # TODO: if market sell fullfilled, we should cancel the trailing stop from entering the position...

                if execute:  # We should get transaction ID, so we can track the open orders...
                    print(f"MarketOrder returned : {mo}")
                    #print(f"StopLossOrder returned : {mo}")

                LOGGER.info(f"Bullish Strategy Terminated.")
                return

            except Exception as e:
                except_count +=1
                LOGGER.error(f"Exception caught : {e}.", exc_info=True)

                # TODO :FIX this : need to be passed to recursive call
                # if except_count < 3:
                #     LOGGER.warning(f"Retrying...")
                # else:
                raise
        else:
            # TODO : move the stop loss target (client-side trailing stop)
            if stop_loss_order:
                oo = await self.rest_client_proxy.openorders()
                print(oo)  # NOTE : We need execute = True to get anything here...

                if stop_loss_order in oo:
                    # get stop loss order price
                    stop_loss_price_old = oo[stop_loss_order].descr.price

                    # # attempt to lock in enter price  # TODO : probably bad idea... we need some room to oscillate before locking in fees...
                    # if stop_loss_price_old < enter_price < price:
                    #     print(
                    #         f"current price higher than enter price: {price} > {enter_price}...")
                    #
                    #     # pass new order with updated price (should be higher)
                    #     slo = await self.rest_client_proxy.addorder(
                    #         RequestOrder(pair=self.pair).stop_loss(stop_loss_price=enter_price).sell(
                    #             volume=volume).execute(execute))
                    #     print(f"new stop loss {slo} created.")
                    #
                    #     # cancel old stop loss order
                    #     # CAREFUL : too many cancels will get you locked out !
                    #     cancelled = await self.rest_client_proxy.cancelorder(stop_loss_order)
                    #     print(f"old stop loss {stop_loss_order} cancelled: {cancelled}.")
                    #     stop_loss_order = slo.get('txid')
                    #
                    # else:
                    # attempt to lock in fees
                    stop_loss_price_new = round(enter_price * Decimal(1.0026), self.pairinfo.pair_decimals)
                    if stop_loss_price_old < enter_price < stop_loss_price_new < price:

                        print(
                            f"current price higher than enter price + fees: {price} > {stop_loss_price_new}...")

                        # pass new order with updated price (should be higher)
                        slo = await self.rest_client_proxy.addorder(
                            RequestOrder(pair=self.pair).stop_loss(stop_loss_price=stop_loss_price_new).sell(
                                volume=volume).execute(execute))
                        print(f"new stop loss {slo} created.")

                        # cancel old stop loss order
                        # CAREFUL : too many cancels will get you locked out !
                        cancelled = await self.rest_client_proxy.cancelorder(stop_loss_order)
                        print(f"old stop loss {stop_loss_order} cancelled: {cancelled}.")
                        stop_loss_order = slo.get('txid')
                else:
                    print(f"Stop loss order not in Open Orders")
                    print(f"=> Stop loss has been triggered. Ending strategy.")
                    return

            LOGGER.debug(f"RSI: \n{rsi}")
            LOGGER.info(f"RSI: {rsi.iloc[-1]['RSI_14']} sleeping for a bit...")
            await asyncio.sleep(10)
            # looping...
            return asyncio.create_task(self(volume=volume, execute=execute, enter_price=enter_price, stop_loss_order=stop_loss_order))
        # exit and die.


async def bullbot(loop, proxy, pair="XBTEUR", pairinfo = None):
    try:

        bull_enter = OrderEnterBullishStrategy(rest_client_proxy=proxy, pair=pair, pairinfo=pairinfo)

        task_gen = await bull_enter(volume=Decimal(0.01),
                                 # obvious CPS... TODO : better design ?
                   callonexit= OrderExitBullishStrategy(rest_client_proxy=proxy, pair=pair, pairinfo=pairinfo),
                   execute=True)
        ### Main execute point for now (TESTING)

        while task_gen:
            LOGGER.debug(f"Waiting for sequence of tasks...")
            # waiting for sequence of tasks monoid style...
            if not task_gen.done():
                await asyncio.sleep(5.0)
            else:  # expectation : the task return another task, or None...
                task_gen = task_gen.result()

        # no tasks left -> exiting # TODO : tracking profit ??
    except Exception as e:
        LOGGER.error(f"Exception caught in bullbot : {e}. Terminating...", exc_info=True)
        raise
    finally:
        # TODO : cleaning up bot data, cancel left over orders, etc.
        # Making sure our previous stop loss is gone
        oo = await proxy.openorders()
        print(f"Orders left open after strategy run: \n{oo}")


async def basicbot(loop):

    from aiokraken.config import load_api_keyfile
    keystruct = load_api_keyfile()
    rest_kraken = RestClient(server=Server(key=keystruct.get('key'),
                                           secret=keystruct.get('secret')))
    try:

        proxy = Proxy(rest_client=rest_kraken)
        # seems we can reuse the proxy here... (still same account on same exchange)
        while True:
            # : For now we pick a pair manually...
            assets = (await proxy.assets(assets=["XBT", "EUR"]))

            assetpairs = (await proxy.assetpairs(assets=["XBTEUR"]))

            bullbot_run = await bullbot(loop=asyncio.get_event_loop(),
                              proxy=proxy,
                              pair="XBTEUR", pairinfo=assetpairs["XXBTZEUR"])
            if bullbot_run:
                await asyncio.wait([bullbot_run], loop=loop, return_when=asyncio.ALL_COMPLETED)

    except Exception as e:
        LOGGER.error(f"Exception caught : {e}. Terminating...", exc_info=True)
        raise
    finally:
        # TODO : cleanup (cancel all tasks, maybe cancel orders, etc.)
        await rest_kraken.close()


loop = asyncio.get_event_loop()

for signame in ('SIGINT', 'SIGTERM'):
    loop.add_signal_handler(
        getattr(signal, signame),
        lambda: asyncio.ensure_future(ask_exit(signame))
    )

loop.run_until_complete(basicbot(loop))
