
# One and only one per process, ie per module (instantiated in interpreter)
import asyncio
import contextlib
import functools
import signal

import aiohttp
import typing


_headers = {
    'User-Agent': 'aiokraken'
}

# Only one session per process (one in this module, instantiated by interpreter on import)
_single_session: typing.Optional[aiohttp.ClientSession] = None


def unified_session_context() -> typing.AsyncContextManager:
    global _single_session
    if _single_session is None:
        # Note : async loop must already be running here.
        _single_session = aiohttp.ClientSession(headers=_headers, raise_for_status=True)
    return _single_session


# Note maybe we should use the session for both websockets and rest...

if __name__ == '__main__':

    async def main():

        async with unified_session_context() as s:
            print("infinite loop. ctrl-c to trigger keyboard interrupt and exit.")
            while True:
                await asyncio.sleep(1)

    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    try:
        loop.run_until_complete(main())

    # KeyboardInterrupt (and system existing exceptions) are caught outside the loop first !
    except KeyboardInterrupt as ki:
        print("out of loop already")
    finally:

        print("finalizing loop to handle context and exceptions...")
        # this is necessary for the loop to finalize its contexts and do exception handling !
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()
