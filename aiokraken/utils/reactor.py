import asyncio
import types

import time
from dataclasses import dataclass

from entities import Entity

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
            r = []  # generator currently makes problems with how the world turns around...
            # plus doing all entities at once for one system can make sense...
            # TODO: should ultimately be up to the world...
            for e in entities:
                r.append(await fun(e[component_class], deltatime = dt))
            last_time = t
            return r

        return reactor_wrapper  # returning Reactor doesnt work ??

    return reactor_decorator


if __name__ == '__main__':

    import asyncio

    # Usage example
    # Basic component definition
    @dataclass
    class Compo:
        answer: str = '42'

    # Basic system definition
    @reactor(Compo)
    async def reacdemo(comp, **kwargs):  # kwargs is used to pass around "side-effect" stuff... (scheduling, memory, profiling, etc.)
        print(comp)
        await asyncio.sleep(0.1)

    loop = asyncio.get_event_loop()

    world = [Entity(Compo('51')), ]

    # scheduling call just once, for testing...
    loop.run_until_complete(  # loop
        reacdemo(  # system update as coroutine
            Entity(Compo('51'))  # passing one entity only (decorator will extract the components)
        )
    )
    # normally, a reactor would be called by the environment instead...


