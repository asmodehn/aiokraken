import aiohttp
import asyncio
import signal

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from aiokraken.rest.client import RestClient

from aiokraken.model.order import MarketOrder, StopLossOrder, TrailingStopOrder, ask, bid

LOGGER = get_kraken_logger(__name__)


# Dummy client
# TODO : command line basic client.

async def get_time():
    """ get kraken time"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.time()
        print(f'response is {response}')
    finally:
        await rest_kraken.close()


async def get_balance():
    """Start kraken websockets api
    """
    from aiokraken.config import load_api_keyfile
    keystruct = load_api_keyfile()
    rest_kraken = RestClient(server=Server(key=keystruct.get('key'),
                                           secret=keystruct.get('secret')))
    response = await rest_kraken.balance()
    await rest_kraken.close()
    print(f'response is {response}')


@asyncio.coroutine
def ask_exit(sig_name):
    print("got signal %s: exit" % sig_name)
    yield from asyncio.sleep(1.0)
    asyncio.get_event_loop().stop()


def check_rsi(rest_client, pair):
    response = await rest_client.ohlc(pair=pair)
    print(f'response is \n{response.head()}')

    indicators = response.rsi()

    print(f'with RSI indicator \n{indicators.head()}')
    return indicators


class Position:
    """ Note this is the abstract concept of position (aggregation of trades).
        It is related, but not exactly the same as the exchange's position.
        More specifically : it conceptually exists, even if leverage is 0.
    """

    def __init__(self, rest_client, enter_order, stoploss):
        self.rest_client = rest_client
        self.entering_order = enter_order
        self.stoploss = stoploss
        self.pair = self.entering_order.pair

        # TODO : add entering logic
        response = await self.rest_client.ask(order=self.entering_order)

        # trailing stop
        stop_response = await self.rest_client.ask(order=self.stoploss)

        if self.entering_order.type == 'buy':
            self.long = True
            self.short = False
        elif self.entering_order.type == 'sell':
            self.short = True
            self.long = False

    async def __call__(self, *args, **kwargs):
        """
        Looping coro managing the position
        :param args:
        :param kwargs:
        :return:
        """
        # TODO : replace this by Websockets callback...

        indicators = check_rsi(rest_client=self.rest_client, pair=self.pair)

        if indicators < 60 and self.long:
            self.settle(ask(MarketOrder(pair=self.pair, volume=self.entering_order.volume)))

        elif indicators > 30 and self.short:
            self.settle(bid(MarketOrder(pair=self.pair, volume=self.entering_order.volume)))

    def settle(self, leave_order):
        response = await self.rest_client.ask(order=leave_order)

    def cancel(self, cancel_order):
        response = await self.rest_client.ask(order=cancel_order)


async def basicbot(loop, pair= 'XBTEUR'):

    from aiokraken.config import load_api_keyfile
    keystruct = load_api_keyfile()
    rest_kraken = RestClient(server=Server(key=keystruct.get('key'),
                                           secret=keystruct.get('secret')))
    try:

        pm = None

        # self test to make sure everything is working, as early as possible, as much as possible.
        indicators = check_rsi(rest_client=rest_kraken, pair=pair)

        # SelfTest buy case quickly
        pm = Position(rest_client=rest_kraken,
                      enter_order=bid(MarketOrder(pair=pair, volume='0.01')),
                      stoploss=StopLossOrder(pair=pair, stop_loss_price="-5"))
        pm.settle(leave_order=ask(MarketOrder))
        pm = None

        # SelfTest sell case quickly
        pm=Position(
        )
        pm.settle()
        pm = None

        # while True:
        #     indicators = check_rsi(rest_client=rest_kraken, pair=pair)
        #
        #     if indicators > 60 and pm is None:
        #         # bull trend
        #         pm = Position()  # todo : some kind of basic risk management ?
        #
        #
        #     elif indicators < 30 and pm is None:
        #         # bear trend
        #         pm = Position()  # todo : some kind of basic risk management ?
        #
        #
        #     bull_detector = loop.create_task(
        #         bull(pair='XBTEUR',
        #              enter=bid(),
        #              leave=ask()))
        #     bear_detector = loop.create_task(
        #         bear(pair='XBTEUR',
        #              enter=ask(),
        #              leave=bid()))
        #     await asyncio.wait([bull_detector, bear_detector], loop=loop, return_when=asyncio.ALL_COMPLETED)
        #     await asyncio.sleep(10)
    finally:
        await rest_kraken.close()


loop = asyncio.get_event_loop()

for signame in ('SIGINT', 'SIGTERM'):
    loop.add_signal_handler(
        getattr(signal, signame),
        lambda: asyncio.ensure_future(ask_exit(signame))
    )

loop.run_until_complete(basicbot(loop))
