import time
from datetime import timedelta
from decimal import Decimal, localcontext, DefaultContext

import aiohttp
import asyncio
import signal

from aiokraken import Markets, Balance, OHLC

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from aiokraken.rest.client import RestClient

from aiokraken.model.timeframe import KTimeFrameModel


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


async def basicbot(assets_allowed, assets_forbidden, markets_allowed, markets_forbidden, loop):

    from aiokraken.config import load_api_keyfile
    keystruct = load_api_keyfile()

    # public
    pub_client = RestClient(server=Server())
    # TODO : use interface client (REST + WS) when ready
    priv_client = RestClient(server=Server(
        key=keystruct.get('key'),
        secret=keystruct.get('secret')
    ))

    markets = Markets(restclient = priv_client)
    # Note : now that self.restclient has markets has trades and orders, we need to use private client...
    markets.filter(whitelist=markets_allowed, blacklist=markets_forbidden)

    balance = Balance(restclient = priv_client)
    balance.filter(whitelist=assets_allowed, blacklist=assets_forbidden)

    try:
        # update the different markets to find suitable ones
        await markets()

        while True:

            # get balance to find out tradable pairs
            await balance()

            print(balance)

            # get tradable markets without leverage
            tradables = {t: m for t, m in markets.details.items() if m.base in balance}

            print(tradables)

            flat_markets = list()  # not interesting ones

            for m, data in {m: d for m, d in markets.items() if m in tradables}.items():
                # TODO : context manager for timeframe ?

                mdata = await data(KTimeFrameModel.one_minute)  # update at specific timeframe to find interesting markets

                if (mdata.tf_ohlc[KTimeFrameModel.one_minute].high == mdata.tf_ohlc[KTimeFrameModel.one_minute].low):
                    # nothing happened there, drop it
                    print(f"{m} looks flat. Dropping it.")
                    flat_markets.append(m)
                else:
                    # TODO : maybe check trend via open/close onf the whole ohlc ?

                    # TODO : maybe each strategy has its preconditions to validate before even attempting it...
                    pivot = mdata.tf_ohlc[KTimeFrameModel.one_minute].pivot(before=timedelta(days=1))

                    print(f"Resistances / Supports for {m}: {pivot}")

                    # select markets based on pivot data:
                    if pivot.R1 - pivot.S1 < pivot.pivot * 0.0025:  # check if the interval is bigger than fees
                        flat_markets.append(m)
                        print(f"{m} Support Resistance interval data too flat to cover fees. Dropping it.")
                        # TODO : put signals in place to re-add it to the list of interesting markets if interval increase...
                    else:
                        # TODO : maybe lazy update of data only when required ? how to keep managing async control ?
                        #  Think multiple agents, one per strategy... ( can access one or more markets... )
                        #  NB:  they might use the (immutable or time-updated only -> deterministic) data,
                        #    even if requested by another...
                        ema = mdata.tf_ohlc[KTimeFrameModel.one_minute].ema(name="EMA_12", length=12)

                        # TODO : simplify accessor...
                        # get last EMA value
                        print(f" Last EMA_12 for {m}: {ema.model.timedataframe.iloc[-1]}")

                    # STRATEGIES
                    # Daytrade ->  FIRST FOCUS : restart every night. no point in keeping data for long.
                    # TODO : adjust timeframe.
                    # Position ->  NEXT
                    # swing -> later
                    # scalping -> later

                    # Day trading strats :
                    # - pivot / support / resistance DONE !
                    # - trend  TODO
                    # - fibonnacci levels TODo
                    # - breakout  https://tradingsim.com/blog/day-trading-breakouts/
                    # - reversal  https://www.investopedia.com/terms/r/reversal.asp
                    # - momentum



                    # TODO : Automated trading plan https://www.investopedia.com/terms/t/trading-plan.asp
                    # Setup Tradesignals

                    #TODO

                    # if ohlc[m]
                    #
                    #
                    # def obv_crossover():
                    #     raise NotImplementedError
                    #
                    # def r1_crossover():
                    #     raise NotImplementedError
                    #
                    # ohlc[m].obv.crossover(obv_crossover)
                    # ohlc[m].R1.crossover(r1_crossover)

                    # Ref : https://tradingstrategyguides.com/best-bitcoin-trading-strategy/
                    # Ref : https://tradingstrategyguides.com/support-and-resistance-strategy/
                    # TODO: On combination of signal : setup orders + setup signals on order filled.

            if flat_markets:
                markets.filter(blacklist=flat_markets)  # adding flat markets to blacklist for next loop

    except Exception as e:
        LOGGER.error(f"Exception caught : {e}. Terminating...", exc_info=True)
        raise

    # TODO : backtest on previous day before implementing on current day... => need candles from Day -2
    #  Goal : choose markets that are likely to be profitable (given fee calculations).


if __name__ == '__main__':

    from configparser import ConfigParser
    config = ConfigParser()
    config.read("example.ini")

    loop = asyncio.get_event_loop()

    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(
            getattr(signal, signame),
            lambda: asyncio.ensure_future(ask_exit(signame))
        )

    loop.run_until_complete(basicbot(
        assets_allowed=config["assets"]['whitelist'].split(),
        assets_forbidden=config["assets"]["blacklist"].split(),
        markets_allowed=config["markets"]["whitelist"].split(),
        markets_forbidden=config["markets"]["blacklist"].split(),
        loop=loop
    ))
