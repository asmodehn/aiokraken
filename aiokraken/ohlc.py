import asyncio

from aiokraken import RestClient
from aiokraken.model.ohlc import OHLC
from aiokraken.rest import Server


from aiokraken.config import load_account_persist
from aiokraken.rest import RestClient, Server
from aiokraken.timeframe import TimeFrame
from collections.abc import Mapping


class OHLC:

    def __init__(self,): # timeframe:TimeFrame ):
        # self.timeframe = timeframe
        self.impl = None
        pass

    async def __call__(self, rest_client):
        """
        """
        rest_client = rest_client or RestClient()
        ohlc_run = rest_client.ohlc()  # TODO : timeframe...
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

    # TODO : maybe we should keep iter design for time dependent collections (OHLC, timeseries, etc.)
    #     And have key addressing only for time independent collections (index is obvious for humans - not a cryptic timestamp)...
    def __iter__(self):
        # Ref : https://thispointer.com/pandas-6-different-ways-to-iterate-over-rows-in-a-dataframe-update-while-iterating-row-by-row/
        return iter(self.impl)

    def __len__(self):
        return len(self.impl)


if __name__ == '__main__':

    async def assets_retrieve_nosession():
        rest = RestClient(server=Server())
        ohlc = OHLC()
        await ohlc(rest_client=rest)
        for k in ohlc:
            print(f" - {k}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(assets_retrieve_nosession())

    loop.close()

