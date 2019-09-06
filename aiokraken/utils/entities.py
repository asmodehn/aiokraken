

"""
An Entity ( as in Entity Component System design ).
"""
import signal
import asyncio
import uuid
import enum


class Entity:  # Should be a very simple record.

    def __init__(self, *components):
        self.id = uuid.uuid4()  # is this actually useful ?
        # TODO : Some better /more optimized way ?
        self.components = dict()
        # filling in the components
        for c in components:
            self.components[type(c)] = c

    def __hash__(self):
        """ Unique Id for entity """
        return hash((self.id, self.components))

    # iterable interface over values
    def __iter__(self):
        return (c for c in self.components.values())

    # but item access via type
    def __getitem__(self, item):
        return self.components.get(item)

    # TODO : getattr to component dict...

# Idea : world is tied to process/interpreter execution lifecycle


def reset(*entities, loop=None):
    loop = loop or asyncio.get_event_loop()

    def reset_decorator(coro):
        """ decorator declaring a reset coroutine"""

        return loop.create_task(coro(*entities))

    return reset_decorator

# Note we need reset for coroutines.
# But for usual functions, they can be run on import if they are used as decorators in code.


def on_signal(*sigs: enum.Enum, loop=None):
    loop = loop or asyncio.get_event_loop()

    # Note we make this a coro to be use in reset (and be generic)
    def on_signal_decorator(coro):
        for sig in sigs:
            loop.add_signal_handler(sig,  # Note : sig must be an enum (since python 3.5)
                # Even if we setup reset *functions*, we need to call coroutines to schedule them in the loop....
                callback = lambda: asyncio.ensure_future(coro(sig))
            )

    # Note on_signal_decorator is run on import -> no need to add to reset list.
    return on_signal_decorator



# This is setup on import as mandatory default for safety
# Note : redefining could override ? or not ? TODO
@on_signal(signal.SIGINT, signal.SIGTERM)
async def ask_exit(sig_name):
    print("got signal %s: exit" % sig_name)
    await asyncio.sleep(2.0)
    asyncio.get_event_loop().stop()


if __name__ == '__main__':
    # very basic, doing nothing world running...

    print("entities.py running event loop... use SIGTERM | SIGINT to stop it.")

    # lifeloop
    asyncio.get_event_loop().run_forever()

    # signal handler should kill this
