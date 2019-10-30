import time
from decimal import Decimal

import aiohttp
import asyncio
import signal

from aiokraken.rest.schemas.kcurrency import KCurrency
from aiokraken.rest.schemas.kpair import PairModel
from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from aiokraken.rest.client import RestClient

from aiokraken.rest.schemas.krequestorder import RequestOrder
from aiokraken.rest.schemas.kopenorder import KOpenOrderModel

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

        self._last_private_call = time.time()
        self._last_balance = None
        LOGGER.info(f"Proxy created. time: {int(time.time())}")

    async def ticker(self, pairs, wait_for_it = False):
        now = time.time()
        # CAREFUL with timer, we cannot limit restart of software !
        # Better to start slowly, just in case...
        if self._last_ticker is None or (wait_for_it and now - self._last_public_call < self.public_period_limit):
            await asyncio.sleep(self.public_period_limit - now + self._last_public_call)
        if self._last_ticker is None or now - self._last_public_call > self.public_period_limit:
            self._last_public_call = now
            self._last_ticker = await self.rest_client.ticker() #pair=pairs)  # TODO :FIXIT to pass the pair...
            LOGGER.info(f"Ticker for {pairs}: {self._last_ticker}")

        res = self._last_ticker
        return res

    async def ohlcv(self, pair, wait_for_it = False):
        now = time.time()
        # CAREFUL with timer, we cannot limit restart of software !
        # Better to start slowly, just in case...
        if self._last_ohlcv is None or (wait_for_it and now - self._last_public_call < self.public_period_limit):
            await asyncio.sleep(self.public_period_limit - now + self._last_public_call)
        if self._last_ohlcv is None or now - self._last_public_call > self.public_period_limit:
            self._last_public_call = now
            self._last_ohlcv = await self.rest_client.ohlc(pair=pair)
            LOGGER.info(f"OHLCV for {pair} : {self._last_ohlcv}")

        res = self._last_ohlcv
        return res

    async def balance(self, wait_for_it = False):  # Note : the wait_for_it is not about public/private, but about GET/POST behavior...
        now = time.time()
        if self._last_balance is None or (wait_for_it and now - self._last_private_call < self.private_period_limit):
            await asyncio.sleep(self.private_period_limit - now + self._last_private_call)
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
        if now - self._last_private_call < self.private_period_limit:
            await asyncio.sleep(self.private_period_limit - now + self._last_private_call)
        if now - self._last_private_call > self.private_period_limit:
            self._last_private_call = now
            response = await self.rest_client.addorder(order=order)
            LOGGER.info(f"AddOrder API called with {order}")
            LOGGER.info(f"-> {response}")
            # self_orders.append = res  # TODO : order manager
            return response
        return None  # Note: proxying response here does not make any sense

    async def cancel(self, txid):
        res = None
        now = time.time()
        if now - self._last_private_call < self.private_period_limit:
            await asyncio.sleep(self.private_period_limit - now + self._last_private_call)
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

    def __init__(self, rest_client_proxy, pair):
        self.rest_client_proxy = rest_client_proxy
        self.pair = pair

    async def __call__(self, volume, exit_coro):
        # wait for the right moment

        ohlc = await self.rest_client_proxy.ohlcv(pair=self.pair)
        ohlc.rsi()
        rsi = ohlc.dataframe[['time', 'RSI_14']]  # getting last RSI value

        # making sure the time of the measure
        assert int(time.time()) - rsi.iloc[-1]['time'] < 100  # expected timeframe of 1 minutes by default  # TODO : manage TIME !!!

        if rsi.iloc[-1]['RSI_14'] > 40:  # TMP DEBUG 60:
            LOGGER.info(f"RSI: \n{rsi}. Commencing Bullish strategy...")
            ticker = await self.rest_client_proxy.ticker(pairs=self.pair)
            # extract current price as midpoint of bid and ask from ticker
            price = (ticker.ask.price + ticker.bid.price) / 2
            LOGGER.info(f"Price for {self.pair}: {price}. Passing Enter Order ...")
            # bull trend
            # TODO : how to pass 2 orders quicker (more " together") ??
            await self.rest_client_proxy.addorder(RequestOrder(pair=self.pair).market().bid(volume=volume))
            await self.rest_client_proxy.addorder(RequestOrder(pair=self.pair).stop_loss(stop_loss_price=price * Decimal(0.95)))

            # trigger exit strat
            LOGGER.info(f"Triggering Exit watch...")
            return asyncio.create_task(exit_coro)

            # exit and die.

        else:
            LOGGER.info(f"RSI: \n{rsi}. sleeping for a bit...")
            await asyncio.sleep(10)
            # looping...
            return asyncio.create_task(self(volume=volume, exit_coro=exit_coro))


class OrderExitBullishStrategy:
    """
    Elementary strategy
    """

    def __init__(self, rest_client_proxy, pair):
        self.rest_client_proxy = rest_client_proxy
        self.pair = pair

    # TODO : design review : same volume, 'exit' behavior could retrigger 'enter' behavior...
    #  and we wouldnt need a supervisor...
    async def __call__(self, volume):
        # wait for the right moment

        ohlc = await self.rest_client_proxy.ohlcv(pair=self.pair)
        ohlc.rsi()
        rsi = ohlc.dataframe[['time', 'RSI_14']][-1]  # getting last RSI value

        # making sure the time of the measure
        assert int(time.time()) - rsi.iloc[-1]['time'] < 100  # expected timeframe of 1 minutes by default  # TODO : manage TIME !!!

        if rsi.iloc[-1]['RSI_14'] < 40:  # 60 TMP DEBUG
            LOGGER.info(f"RSI: \n{rsi}. Terminating Bullish strategy...")
            ticker = await self.rest_client_proxy.ticker(pairs=self.pair)
            # extract current price as midpoint of bid and ask from ticker
            price = (ticker.ask.price + ticker.bid.price) / 2

            LOGGER.info(f"Price for {self.pair}: {price}. Passing Exit Order ...")
            # Not bull any longer : pass the inverse/complementary order...
            # TODO : how to pass 2 orders quicker (more " together") ??
            await self.rest_client_proxy.addorder(RequestOrder(pair=self.pair).market().sell(volume=volume))
            await self.rest_client_proxy.addorder(RequestOrder(pair=self.pair).stop_loss(stop_loss_price=price * Decimal(1.05)))

            LOGGER.info(f"Bullish Strategy Terminated.")
        else:
            LOGGER.info(f"RSI: \n{rsi}. sleeping for a bit...")
            await asyncio.sleep(10)
            # looping...
            asyncio.create_task(self(volume=volume))
        # exit and die.


async def bullbot(loop, proxy, pair=PairModel(base=KCurrency.XBT, quote=KCurrency.EUR)):
    try:

        bull_enter = OrderEnterBullishStrategy(rest_client_proxy=proxy, pair=pair)

        task_gen = await bull_enter(volume=Decimal(0.01),
                                 # obvious CPS... TODO : better design ?
                   exit_coro= OrderExitBullishStrategy(rest_client_proxy=proxy, pair=pair)(
                       volume=Decimal(0.01))
                   )

        while task_gen:
            LOGGER.info(f"Waiting for sequence of tasks...")
            # waiting for sequence of tasks monoid style...
            if not task_gen.done():
                await asyncio.sleep(5.0)
            else:  # expectation : the task return another task, or None...
                task_gen = task_gen.result()

        # no tasks left -> exiting # TODO : tracking profit ??

    finally:
        # TODO : cleaning up bot data
        pass


async def basicbot(loop, pair=PairModel(base=KCurrency.XBT, quote=KCurrency.EUR)):

    from aiokraken.config import load_api_keyfile
    keystruct = load_api_keyfile()
    rest_kraken = RestClient(server=Server(key=keystruct.get('key'),
                                           secret=keystruct.get('secret')))
    try:

        proxy = Proxy(rest_client=rest_kraken)
        # seems we can reuse the proxy here... (still same account on same exchange)
        while True:
            bullbot_run = await bullbot(loop=asyncio.get_event_loop(),
                              proxy=proxy,
                              pair=pair)
            await asyncio.wait([bullbot_run], loop=loop, return_when=asyncio.ALL_COMPLETED)
    except Exception as e:
        LOGGER.info(f"Exception caught : {e}. Terminating...")
    finally:
        await rest_kraken.close()


loop = asyncio.get_event_loop()

for signame in ('SIGINT', 'SIGTERM'):
    loop.add_signal_handler(
        getattr(signal, signame),
        lambda: asyncio.ensure_future(ask_exit(signame))
    )

loop.run_until_complete(basicbot(loop, pair=PairModel(base=KCurrency.XBT, quote=KCurrency.EUR)))
