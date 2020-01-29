import time
from decimal import Decimal, localcontext, DefaultContext

import aiohttp
import asyncio
import signal

from aiokraken import Markets, Balance, OHLC

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from aiokraken.rest.client import RestClient

from aiokraken.rest.schemas.krequestorder import RequestOrder
from aiokraken.rest.schemas.kopenorder import KOpenOrderModel
from aiokraken.rest.schemas.korderdescr import KOrderDescrOnePrice, KOrderDescr

LOGGER = get_kraken_logger(__name__)


# Stupid bot

@asyncio.coroutine
def ask_exit(sig_name):
    print("got signal %s: exit" % sig_name)
    yield from asyncio.sleep(1.0)
    asyncio.get_event_loop().stop()




# TODO : related to the command design pattern?

# Ref for coroutine execution flow...
# https://stackoverflow.com/questions/30380110/mutually-recursive-coroutines-with-asyncio


# class Box:
#
#     start: Event  # an event is  a signal that has been triggered: it has happened
#     stop:  Event
#     low:   decimal.Decimal
#     high:  decimal.Decimal
#
#
#
# def square_bull(ohlc: OHLC, start: Signal, stop: Signal):
#
#     boxes = []
#
#     # TODO : extract boxes from ohlc dataframe
#
#
#     return boxes


async def basicbot(loop):

    from aiokraken.config import load_api_keyfile
    keystruct = load_api_keyfile()

    # public
    pub_client = RestClient(server=Server())
    # TODO : use interface client (REST + WS) when ready
    priv_client = RestClient(server=Server(
        key=keystruct.get('key'),
        secret=keystruct.get('secret')
    ))

    markets = Markets(restclient = pub_client)
    # TODO : configure this...

    # TODO : configure this...
    balance = Balance(restclient = priv_client)

    await markets()
    # Preparing OHLC instance for all markets
    ohlc = dict()
    for m in markets:
        ohlc[m] = OHLC(pair=m, restclient= pub_client)

    try:
        # update the different markets to find suitable ones
        await markets()

        while True:

            # get balance to find out tradable pairs
            await balance()

            print(balance)

            tradables = {t: m for t, m in markets.items() if m.base in balance}

            print(tradables)

            # TODO : maybe preorder of currencies to decide which way to trade...
            for m in tradables:
                await ohlc[m]()  # force update for markets that we are interested in trading

                # TODO Simple Analysis
                print(ohlc[m])

                #bullboxes = square_bull(ohlc, start=Signal('EMA_12', 'crossover', 'EMA_24'))

                # Get EMA / MACD cross points

                # Get percent differences in these interval.

                # Keep markets that are over 0.26 * 2 for simple market order strategy

                    # Then Get average underprice before reaching satisfying percentage to setup stoploss



                # TODO: Then markets that are over 0.26 + 0.14 for market enter, limit exit

                # TODO: Then markets that are over 0.14 +0.14 for limit enter, limit exit




            #
            # # : For now we pick a pair manually...
            # assets = (await rest_kraken.assets(assets=["XBT", "EUR"]))
            #
            # assetpairs = (await rest_kraken.assetpairs(assets=["XBTEUR"]))
            #
            # # Here we have a logic based on a position (enter and exit, in this sequence).
            # # This is good for learning automation at a basic level, but can be limiting for human traders...
            # # TODO : maybe simpler strategy :
            # #   - Define a capital that can be engaged per market / per strategy (configuration for market - absolute or relative -, in code for strategy ?)
            # #   - Define buy signal and sell signal ( Note : we could add some basic learning control system there...)
            # #   - run in a loop...
            # #   Note : This doesnt involve any concept of Position tracking.
            # #   => Better for humans and when higher level understanding is required (arbitrage, etc.) and/or available (external profit verification, etc.)
            #
            # bullbot_run = await bullbot(loop=asyncio.get_event_loop(),
            #                   rest_client=rest_kraken,
            #                   pair="XBTEUR", pairinfo=assetpairs["XXBTZEUR"])
            # if bullbot_run:
            #     # TODO : here we should evaluate performance on various pairs, and remove the unperforming ones...
            #     # Note : Running on multiple pairs in parallel seems overkill without proper design to manage the complexity.
            #     # TODO aioecs / pyrlang / smthg... in boken.
            #     await asyncio.wait([bullbot_run], loop=loop, return_when=asyncio.ALL_COMPLETED)

    except Exception as e:
        LOGGER.error(f"Exception caught : {e}. Terminating...", exc_info=True)
        raise


loop = asyncio.get_event_loop()

for signame in ('SIGINT', 'SIGTERM'):
    loop.add_signal_handler(
        getattr(signal, signame),
        lambda: asyncio.ensure_future(ask_exit(signame))
    )

loop.run_until_complete(basicbot(loop))
