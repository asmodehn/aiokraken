import asyncio
import types

import time
from dataclasses import dataclass

from entity import Entity

"""
An type of System ( as in Entity Component System design ).
This type is a Reactor, meaning it is not run by a world, and does not specify when it should be run next (as it doesnt have the knowledge)
It is passive and wait to be scheduled by someone else...
"""


def reactor(component_class):

    def reactor_decorator(fun):
        last_time = 0

        async def reactor_wrapper(*entities, **kwargs):
            nonlocal last_time
            t = time.time()
            dt = t - last_time
            r = await fun(*(e[component_class] for e in entities), deltatime = dt)
            last_time = t
            return r

        return reactor_wrapper  # returning Reactor doesnt work ??

    return reactor_decorator


if __name__ == '__main__':

    import asyncio
    import signal
    from collections import namedtuple

    # Usage example
    # Basic component definition
    @dataclass
    class Compo:
        answer: str = '42'

    # Basic system definition
    @reactor(Compo)
    async def reacdemo(*comps, **kwargs):  # kwargs is used to pass around "side-effect" stuff... (scheduling, memory, profiling, etc.)
        for c in comps:
            print(c)
        await asyncio.sleep(0.1)


    # boiler plate code (would be handled by World somehow)
    @asyncio.coroutine
    def ask_exit(sig_name):
        print("got signal %s: exit" % sig_name)
        yield from asyncio.sleep(2.0)
        asyncio.get_event_loop().stop()

    loop = asyncio.get_event_loop()

    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(
            getattr(signal, signame),
            lambda: asyncio.ensure_future(ask_exit(signame))
        )

    # scheduling call just once for testing...
    loop.run_until_complete(  # loop
        reacdemo(  # system update as coroutine
            Entity(Compo('51'))  # passing one entity only
        )
    )



