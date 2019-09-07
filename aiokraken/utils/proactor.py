"""
An type of System ( as in Entity Component System design ).
This type is a Proactor, meaning it expects to be run by a world, and specify when it should be run next.
It is passive and wait to be scheduled by someone else...
"""
import asyncio

import time

from entities import Entity, reset

from dataclasses import dataclass

if __package__:
    from .reactor import reactor, ReactorWrapper
else:
    from reactor import reactor, ReactorWrapper


class ProactorWrapper(ReactorWrapper):

    # TODO : accept different kinds of trigger, a frequency clock is just a specific one...
    def __init__(self, rate, fun, *component_classes, loop=None):
        self.rate = rate
        self.loop=loop or asyncio.get_event_loop()
        super().__init__(fun, *component_classes)

    async def __call__(self, *entities, **kwargs):

        if self.rate > 0:
            # for scheduling
            await asyncio.sleep(1 / self.rate)  # TODO : fix this to get accurate frequency

        r = await super().__call__(*entities, loop=self.loop, **kwargs)

        if self.rate > 0:
            # proactor will reschedule itself to run asap
            self.loop.create_task(self(*entities, **kwargs))

        return r


def proactor(rate, *component_classes, loop=None):  # rate as Hz # 0 means reactor behavior

    loop = loop or asyncio.get_event_loop()

    def proactor_decorator(fun):

        return ProactorWrapper(rate, fun, *component_classes, loop=loop)

    return proactor_decorator


if __name__ == '__main__':

    import asyncio
    import signal
    from collections import namedtuple

    # Usage example
    # Basic component definition
    @dataclass
    class Compo:
        answer: str = '42'

    # Basic reactor definition
    @reactor(Compo)
    async def reacdemo(*relevant_entities, **kwargs):  # kwargs is used to pass around "side-effect" stuff... (scheduling, memory, profiling, etc.)
        for relevant_entity in relevant_entities:
            print(relevant_entity)
            print(relevant_entity[Compo])
            print(kwargs)
        await asyncio.sleep(0.1)
        return 42  # returning result for some usage later, maybe...


    @dataclass
    class Suffix:
        answer: str = 'a'

    # BAsic proactor definition
    @proactor(2.0, Suffix)
    async def proacdemo(*relevant_entities, loop, **kwargs):
        for relevant_entity in relevant_entities:
            print(relevant_entity)
            print(relevant_entity[Suffix])

            print(kwargs)
            # adding a Compo here and scheduling to trigger a reaction
            relevant_entity[Compo] = Compo('51')

            loop.create_task(reacdemo(*kwargs.get('entities', [])))  ### trigger a reaction TODO : improve

        await asyncio.sleep(0.1)
        return 42  # returning result for some usage later, maybe...


    start_entity = Entity(Suffix('bob'))

    reset(start_entity)(proacdemo)

    asyncio.get_event_loop().run_forever()

