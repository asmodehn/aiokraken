import time
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

    markets = Markets(restclient = pub_client)
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

            for m, data in {m: d for m, d in markets.items() if m in tradables}.items():

                mdata = await data(KTimeFrameModel.one_minute)  # update at specific timeframe to find interesting markets
                # TODO : maybe lazy update of data only when required ?
                ema = mdata.tf_ohlc[KTimeFrameModel.one_minute].ema(name="EMA_12", length=12)

                # TODO : simplify accessor...
                print(f"EMA for {m}: {ema.model.timedataframe.iloc[-1]}")  # get last EMA value for all tradables

                # TODO: enable periodic check of indicators.
                #   signals later...


                # STRATEGIES
                # Daytrade ->  FIRST FOCUS : restart every night. no point in keeping data for long. TODO : adjust timeframe.
                # Position ->  NEXT
                # swing -> later
                # scalping -> later

                # Day trading strats :
                # - pivot / support / resistance FIRST FOCUS
                # - trend  TODO
                # - fibonnacci levels TODo
                # - breakout  https://tradingsim.com/blog/day-trading-breakouts/
                # - reversal  https://www.investopedia.com/terms/r/reversal.asp
                # - momentum

                # TODO : add this to OHLC ( basis of many plans in addition of other indicators... )
                # Ref : https://www.easycalculation.com/finance/pivot-points-trading.php
                # Ref : https://www.investopedia.com/terms/p/pivotpoint.asp
                # Pivot Point = (H + C + L) / 3
                #  R3 = H + 2 x ( Pivot - L )
                #  R2 = Pivot + ( R1 - S1 )
                #  R1 = 2 x Pivot - L
                #  S1 = 2 x Pivot - H
                #  S2 = Pivot - ( R1 - S1 )
                #  S3 = L - 2 x ( H - Pivot )
                #
                # Where,
                # H - Previous Days High
                # L - Previous Days Low
                # C - Previous Days Close
                # R - Resistances Levels
                # S - Supports Levels

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
        assets_allowed=config["assets"]['whitelist'],
        assets_forbidden=config["assets"]["blacklist"],
        markets_allowed=config["markets"]["whitelist"],
        markets_forbidden=config["markets"]["blacklist"],
        loop=loop
    ))
