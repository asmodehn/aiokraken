import asyncio

from aiokraken import RestClient
from aiokraken.model.ohlc import OHLC
from aiokraken.rest import Server


from aiokraken.config import load_account_persist
from aiokraken.rest import RestClient, Server
from aiokraken.model.timeframe import KTimeFrameModel
from aiokraken.timeframe import TimeFrame
from collections.abc import Mapping


class OHLC:

    def __init__(self, pair, timeframe:KTimeFrameModel = KTimeFrameModel.one_minute):
        self.pair = pair
        self.timeframe = timeframe
        self.impl = None
        pass

    async def __call__(self, rest_client):
        """
        """
        rest_client = rest_client or RestClient()
        ohlc_run = rest_client.ohlc(pair=self.pair, interval=self.timeframe)  # TODO : timeframe...
        new_ohlc = (await ohlc_run())

        if new_ohlc:
            if self.impl:
                self.impl = self.impl.stitch(new_ohlc)
            else:
                self.impl = new_ohlc
        return self

    # TODO : howto make display to string / repr ??

    def __getitem__(self, key):
        if self.impl:
            return self.impl[key]
        else:
            # Note : this should not be a keyerror
            raise RuntimeError(f"{self.impl} has not been initialized")

    # TODO : maybe we should keep iter design for time dependent collections (OHLC, timeseries, etc.)
    #     And have key addressing only for time independent collections (index is obvious for humans - not a cryptic timestamp)...
    def __iter__(self):
        # Ref : https://thispointer.com/pandas-6-different-ways-to-iterate-over-rows-in-a-dataframe-update-while-iterating-row-by-row/
        return iter(self.impl)

    def __len__(self):
        if self.impl:
            return len(self.impl)
        else:
            return 0


if __name__ == '__main__':
    import time

    # Client can be global: there is only one.
    rest = RestClient(server=Server())

    # ohlc data can be global (one per market*timeframe only)
    ohlc = OHLC(pair='ETHEUR', timeframe=KTimeFrameModel.one_minute)

    async def ohlc_retrieve_nosession():
        global rest, ohlc
        await ohlc(rest_client=rest)
        for k in ohlc:
            print(f" - {k}")

    loop = asyncio.get_event_loop()

    assert len(ohlc) == 0

    loop.run_until_complete(ohlc_retrieve_nosession())
    assert len(ohlc) == 720, f"from: {ohlc.impl.begin} to: {ohlc.impl.end} -> {len(ohlc)} values"

    print("Waiting one more minute to attempt retrieving more ohlc data and stitch them...")
    time.sleep(60)
    loop.run_until_complete(ohlc_retrieve_nosession())

    assert len(ohlc) == 721,  f"from: {ohlc.impl.begin} to: {ohlc.impl.end} -> {len(ohlc)} values"

    loop.close()

