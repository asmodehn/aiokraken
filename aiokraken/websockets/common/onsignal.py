import asyncio
import contextlib
import functools
import inspect
import json
from dataclasses import dataclass

import aiohttp
import typing

from aiokraken.websockets.schemas.unsubscribe import Unsubscribe, UnsubscribeSchema

from aiokraken.websockets.schemas.subscribe import Subscribe, SubscribeSchema

from aiokraken.utils import get_kraken_logger

LOGGER = get_kraken_logger(__name__)

connections = {}
connections_status = dict()  # TODO : maybe dict is not useful ??

headers = {
    'User-Agent': 'aiokraken'
}
session: typing.Optional[aiohttp.ClientSession] = None

import signal


def onsignal(*sigs: typing.Union[str, int]):
    # accepting the signal code or its name
    sigs = [getattr(signal, s) if isinstance(s, str) else s for s in sigs]

    def decorator(handler):
        # the usual sync case
        for sig in sigs:
            signal.signal(sig, handler)

        # return the decorated function intact
        return handler

    return decorator


import asyncio


def _onsignal_async(loop, *sigs: typing.Union[str, int]):
    # accepting the signal code or its name
    sigs = [getattr(signal, s) if isinstance(s, str) else s for s in sigs]

    def decorator(handler):
        if inspect.iscoroutinefunction(handler):
            # the async usecase, loop existing, but maybe not running
            for sig in sigs:
                loop.add_signal_handler(
                    sig,
                    # we need to evaluate all values now and call ensure_future to run coroutine
                    functools.partial(asyncio.ensure_future, handler(sig))
                )
            # note we do not send the loop, we expect the user site to already have it to use this function

        else:  # the usual sync case but from an eventloop
            for sig in sigs:
                loop.add_signal_handler(
                    sig,
                    # we need to evaluate all values now
                    functools.partial(handler, sig)
                )

        # return the decorated function intact
        return handler

    return decorator


# monkey patch asyncio
asyncio.AbstractEventLoop.onsignal = _onsignal_async


if __name__ == '__main__':
    import time

    sync_loop = True
    async_loop = True

    # SYNC
    @onsignal('SIGINT', signal.SIGTERM)
    def warn(sig, frame=None):
        global sync_loop
        print(f"SYNC run interrupted by {sig} with frame {frame}")
        sync_loop=False
        assert sig == signal.SIGINT

    print("sync running for ever, press ctrl-c")
    while sync_loop:
        time.sleep(1)
        print("still running...")

    loop = asyncio.get_event_loop()

    # ASYNC
    @loop.onsignal('SIGINT', signal.SIGTERM)
    async def async_warn(sig, frame=None):
        global async_loop
        # TODO : pass relevant frame data...
        print(f"ASYNC {loop} run interrupted by {sig} with frame {frame}")
        async_loop = False
        assert sig == signal.SIGINT

    async def asyncloop():
        print("async running for ever, press ctrl-c")
        while async_loop:
            await asyncio.sleep(1)
            print("still running...")

    loop.run_until_complete(asyncloop())
