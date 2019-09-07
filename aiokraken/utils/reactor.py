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


class ReactorWrapper:

    def __init__(self, fun, *component_classes):
        self.fun = fun
        self.component_classes = component_classes
        self.last_time = time.time()

    async def __call__(self, *entities, **kwargs):
        t = time.time()
        dt = t - self.last_time
        # This gives the best control to teh developer:
        # - all entities at once, logically.
        # - awaitable coro for managing systems/entities update synchronization in one place.
        r = await self.fun(
                # filtering to pass only relevant entities to the system.
                *(e for e in entities if all(c in e.components.keys() for c in self.component_classes)),
                deltatime=dt,
                entities=entities,
                **kwargs
            )
        last_time = t
        # this syntax supports both one element and iterable (meaning system call can be either)
        return [r]  # generator cannot be returned at the highest level
        # This is actually where the call is run (need to wait to build the list...)
        # TODO : Meaning this is where we can introduce some profiling later (and not in users code) !



def reactor(*component_classes):

    def reactor_decorator(fun):

        return ReactorWrapper(fun, *component_classes)

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
    async def reacdemo(*relevant_entities, **kwargs):  # kwargs is used to pass around "side-effect" stuff... (scheduling, memory, profiling, etc.)
        for relevant_entity in relevant_entities:
            print(relevant_entity)
            for c in relevant_entity:
                if type(c) == Compo:
                    print(c)
            print(kwargs)
        await asyncio.sleep(0.1)
        return 42  # returning result for some usage later, maybe...

    loop = asyncio.get_event_loop()

    world = [Entity(Compo('51')), ]

    # scheduling call just once, for testing...
    loop.run_until_complete(  # loop
        reacdemo(  # system update as coroutine
            Entity(Compo('51'))  # passing one entity only (decorator will extract the components)
        )
    )
    # normally, a reactor would be called by the environment instead...


