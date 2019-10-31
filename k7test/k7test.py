import asyncio
import aiohttp
import vcr
import logging

logging.basicConfig()  # you need to initialize logging, otherwise you will not see anything from vcrpy
vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.INFO)


async def httpbin_get():
    async with aiohttp.ClientSession() as session:
        with vcr.use_cassette('get_outer.yml', record_mode='all'):  # want to record any traffic, for error debugging purposes...
            with vcr.use_cassette('get_inner.yml', record_mode='once'):  # recorded interraction once. replay during tests.
                async with session.get('http://httpbin.org/get') as resp:
                    print(resp.status)
                    print(await resp.text())

loop = asyncio.get_event_loop()
loop.run_until_complete(httpbin_get())
