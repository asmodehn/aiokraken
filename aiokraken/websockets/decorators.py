"""
A collection of decorators (sync) for pydefs to get called back on websocket messages
"""
import typing

import wrapt
from aiokraken.rest.exceptions import AIOKrakenSchemaValidationException

from aiokraken.websockets.client import WssClient

from aiokraken.model.assetpair import AssetPair


def ticker(pairs: typing.List[AssetPair], client: WssClient = None):
    """ subscribe to the ticker update stream.
    if the returned wrapper is not used, the message will still be parsed,
    until the appropriate wrapper (stored in _callbacks) is called.
    """

    client = client if client is not None else WssClient()

    def decorator(wrpd):

        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            # called on message received
            try:
                wrapped(*args, **kwargs)
            except AIOKrakenSchemaValidationException as aioksve:
                raise  # explicitely forward up to try another schema

        #   we need to create task after decoration to get the wrapped definition

        client.loop.create_task( # TODO : create task or directly run_until_complete ?
            # subscribe
            client.ticker(pairs=pairs, callback=wrapper(wrpd))
        )

        return wrapper(wrpd)

    return decorator


if __name__ == '__main__':
    import asyncio

    from aiokraken.rest import RestClient
    rest_kraken = RestClient()
    # this will retrieve assetpairs and pick the one we want
    xbt_eur = rest_kraken.sync_assetpairs().get("XXBTZEUR")

    @ticker(pairs=[xbt_eur])
    def ticker_update(message):
        print(f'ticker update: {message}')

    @asyncio.coroutine
    def ask_exit(sig_name):
        print("got signal %s: exit" % sig_name)
        yield from asyncio.sleep(2.0)
        asyncio.get_event_loop().stop()

    import signal
    for signame in ('SIGINT', 'SIGTERM'):
        asyncio.get_event_loop().add_signal_handler(
            getattr(signal, signame),
            lambda: asyncio.ensure_future(ask_exit(signame))
        )

    asyncio.get_event_loop().run_forever()
