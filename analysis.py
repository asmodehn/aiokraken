import time
from datetime import timedelta, datetime, timezone
from decimal import Decimal, localcontext, DefaultContext

import aiohttp
import asyncio
import signal

from aiokraken.model.asset import Asset

from aiokraken import markets, balance, ohlc, OHLC

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from aiokraken.rest.client import RestClient

from aiokraken.model.timeframe import KTimeFrameModel


LOGGER = get_kraken_logger(__name__)


"""
A simple script. Duties:
- connect and retrieve market data
- connect and retrieve user/account data
- analyze current held assets (and their previous cost from trades history).
- interactively propose new trades that might be interesting (given some configuration as input)
 MVP : cost of assets, proposes order to recover the cost + fees, and some profit (in the time elapsed between 2 runs)
 
This is a ONE shot script. after one pass, it will end.
HOWEVER the proposed action shall be argumented, enough for a user to decide 
possibly including visual graphs data...
"""


@asyncio.coroutine
def ask_exit(sig_name):
    print("got signal %s: exit" % sig_name)
    yield from asyncio.sleep(1.0)
    asyncio.get_event_loop().stop()


# Ref for coroutine execution flow...
# https://stackoverflow.com/questions/30380110/mutually-recursive-coroutines-with-asyncio

def display(ohlc: OHLC):
    return ohlc.show(block=False)




async def analysisbot(assets_allowed, assets_forbidden, markets_allowed, markets_forbidden,
                        minimize, maximize, lastrun, loop):

    from aiokraken.config import load_api_keyfile
    keystruct = load_api_keyfile()

    # public
    pub_client = RestClient(server=Server())
    # TODO : use interface client (REST + WS) when ready
    priv_client = RestClient(server=Server(
        key=keystruct.get('key'),
        secret=keystruct.get('secret')
    ))

    mkts = await markets(restclient = priv_client)
    # Note : now that self.restclient has markets has trades and orders, we need to use private client...
    mkts.filter(whitelist=markets_allowed, blacklist=markets_forbidden)

    blnc = await balance(restclient = priv_client)
    blnc.filter(whitelist=assets_allowed, blacklist=assets_forbidden)

    # normalize list of assets
    minimize = [a.restname for _,a in blnc.assets.items() if a.restname in minimize or a.altname in minimize]
    maximize = [a.restname for _,a in blnc.assets.items() if a.restname in maximize or a.altname in maximize]

    try:
        print(blnc)

        # get tradable markets without leverage  # Note: this is potentially for very long term -> no leverage
        tradables = {t: m for t, m in mkts.details.items() if m.base in blnc}

        print(tradables)

        # picking appropriate timeframe...
        now = datetime.now(tz=timezone.utc)
        elapsed_time = now - lastrun
        tf = KTimeFrameModel.one_minute
        for t in KTimeFrameModel:
            # picking a time frame detailed enough, but that gives us double time in one ohlc request
            if t.to_timedelta() < elapsed_time < t.to_timedelta() * 360:
                tf = t
                break

        # TODO : context manager for timeframe ?

        for m, data in {m: d for m, d in mkts.items() if m in tradables}.items():

            if data.pair.base not in minimize + maximize and data.pair.quote not in minimize + maximize:
                tradables.pop(m)
                continue  # skip this one, not sure what to do with it...
            # Note : we might need it for conversion, bu tthen we should load it lazily...

            mdata = await data(tf)  # update at specific timeframe to find interesting markets

            if (mdata.tf_ohlc[tf].high == mdata.tf_ohlc[tf].low):
                # nothing happened there, drop it
                print(f"{m} looks flat. Dropping it.")
                tradables.pop(m)

        # TODO : check open orders to see if we need to make any decision...

        # looping on the tradables left (we already have all relevant ohlc)

        for m, mdata in {m: d for m, d in mkts.items() if m in tradables}.items():

            # TODO : maybe check trend via open/close on the whole ohlc ?

            pivot = mdata.tf_ohlc[tf].pivot(before=elapsed_time)

            # TODO : maybe figure out best timeframe to compute resistance/ supports based on ohlc ???

            print(f"Resistances / Supports for {m}: {pivot}")

            # Ref : https://tradingstrategyguides.com/support-and-resistance-strategy/

            # select markets based on pivot data:
            if pivot.R1 - pivot.S1 < pivot.pivot * 0.0025:  # check if the interval is bigger than fees
                print(f"{m} Support Resistance interval data too flat to cover fees. Dropping it.")
                continue
            else:
                # TODO : maybe lazy update of data only when required ? how to keep managing async control ?
                #  Think multiple agents, one per strategy... ( can access one or more markets... )
                #  NB:  they might use the (immutable or time-updated only -> deterministic) data,
                #    even if requested by another...
                ohlc = mdata.tf_ohlc[tf].ema(name="EMA_12", length=12).ema(name="EMA_26", length=26)

                # TODO : simplify accessor...
                # get last EMA value
                print(f" Last EMAs for {m}: {ohlc.indicators['ema'].model.timedataframe.iloc[-1]}")

            # how does it looks ?
            plt = display(ohlc)

            if mdata.pair.quote in minimize or mdata.pair.base in maximize:

                # maybe try to buy
                last_ema = ohlc.indicators["ema"].model.timedataframe.iloc[-1]
                # check trend
                if last_ema["EMA_12"] > last_ema["EMA_26"]:  # TODO : some minimal different required ?
                    # trend up -> good to buy
                    print(f"==> {m} is trending up...")
                    # calculate good buy limit price
                    print(f"==> {pivot.S1} seems like a good limit price to buy...")
                    # TODO : compare with asset average cost

                    if mdata.pair.quote in blnc and blnc[mdata.pair.quote] > 0:  # REMINDER, we want to minimize our asset in this case
                        # compute average cost basis

                        consc = await consolidated_tradecost(asset=blnc.assets[mdata.pair.quote],
                                                         amount=blnc[mdata.pair.quote], target_asset=blnc.assets[mdata.pair.base], markets=mkts, tf=tf)

                        print(f" This is currently equivalent to {consc}")
                        if pivot.S1 < consc.get(mdata.pair.base, Decimal()):  # TODO : integrate fees in this...
                            # we buy cheaper, do it!
                            print(" We can buy cheaper than it did cost, lets do it !")
                            input("fake (y/n)")
                        else:
                            # errrhhhh, are you sure ??
                            print(" errhh we re gonna loose money here, are you sure ?")
                            input("fake (y/n)")

                    elif mdata.pair.base in blnc:

                        consc = await consolidated_tradecost(asset=blnc.assets[mdata.pair.base],
                                                         amount=blnc[mdata.pair.base], target_asset=blnc.assets[mdata.pair.quote], markets=mkts, tf=tf)

                        print(f" This is currently equivalent to {consc}")
                        if pivot.S1 < consc.get(mdata.pair.quote, Decimal()):
                            # we buy cheaper, do it!
                            print(" We can buy cheaper, lets do it !")
                            input("fake (y/n)")
                        else:
                            # errrhhhh, are you sure ??
                            print(" errhh we re gonna loose money here, are you sure ?")
                            input("fake (y/n)")

                    else:
                        print(f"Cant buy anything, we dont hold either {mdata.pair.base} nor {mdata.pair.quote} !")
                        break

                    # we are still in this loop: we have a cost basis

            elif mdata.pair.quote in minimize or mdata.pair.base in maximize:
                 pass
            # TMP skip until we get proper structure
            #
            #     # how does it looks ?
            #     await ohlc.ashow()
            #
            #     # try to sell
            #     last_ema = ohlc.indicators["ema"].model.timedataframe.iloc[-1]
            #     if last_ema["EMA_12"] < last_ema["EMA_26"]:
            #         # trend up -> good to sell
            #         print(f"==> {m} is trending down...")
            #         # calculate good limit price
            #         print(f"==> {pivot.S1} seems like a good limit price...")
            #         # TODO : compare with asset average cost

            plt.close("all")  # Close currently opened plots
    except Exception as e:
        LOGGER.error(f"Exception caught : {e}. Terminating...", exc_info=True)
        raise

    # TODO : backtest on previous day before implementing on current day... => need candles from Day -2
    #  Goal : choose markets that are likely to be profitable (given fee calculations).


async def consolidated_tradecost(asset: Asset, amount: Decimal, target_asset:Asset, markets, tf):
    # compute average cost basis
    consc =dict()
    c = markets.tradecost(asset=asset, amount=amount)
    print(f"{asset}: {amount} cost from trades is {c}")
    consc.setdefault(target_asset.restname, c.get(target_asset.restname, Decimal()))
    # consolidate in the proper asset
    # HOWTO ? might be overly complicated...
    for n, a in c.items():
        # TODO : better way to look into markets to retrieve price
        if n != target_asset and target_asset.restname + n in markets.details.keys():
            if tf not in markets.get(target_asset.restname + n).tf_ohlc:
                await markets.get(target_asset.restname + n)(tf)  # TODO : nicer interface for marketdata...
            nprice = markets.get(target_asset.restname + n).tf_ohlc.close
            # convert
            consc[n] = consc.get(target_asset.restname, Decimal()) + c[n] / nprice
            # TODO : units (pint) pleaaaaase...
        else:  # cannot convert this, keep it intact to not get a wrong cost
            consc.update({n: a})
    return consc

if __name__ == '__main__':

    from configparser import ConfigParser
    config = ConfigParser()
    config.read("analysis.ini")

    loop = asyncio.get_event_loop()

    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(
            getattr(signal, signame),
            lambda: asyncio.ensure_future(ask_exit(signame))
        )

    assets_ok = set(config["assets"].get('whitelist', "").split())
    assets_block = set(config["assets"].get('blacklist',"").split())
    assets_ok = assets_ok - assets_block
    # TODO : wildcard ?

    markets_ok = set(config["markets"].get('whitelist',"").split())
    markets_block = set(config["markets"].get('blacklist',"").split())
    markets_ok = markets_ok - markets_block
    # TODO : wildcard ?

    loop.run_until_complete(analysisbot(
        assets_allowed=[a for a in assets_ok],
        assets_forbidden=[a for a in assets_block],
        markets_allowed=[m for m in markets_ok],
        markets_forbidden=[m for m in markets_block],
        minimize=config["analysis"]["minimize"].split(),
        maximize=config["analysis"]["maximize"].split(),
        lastrun=datetime.fromisoformat(config["analysis"].get("lastrun",
                                                              (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat())),
        loop=loop
    ))

    if "lastrun" not in config.sections():
        config.add_section('lastrun')
    config.set('lastrun', 'datetime', datetime.now(tz=timezone.utc).isoformat())

    # lets create that config file...
    cfgfile = open("analysis.ini", 'w')
    # reminder : comments will be gone !
    config.write(cfgfile)
    cfgfile.close()
