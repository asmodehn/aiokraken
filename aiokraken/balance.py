import asyncio
from pprint import pprint

from aiokraken.rest import RestClient, Server

from collections.abc import Mapping


class Balance(Mapping):

    def __init__(self, assets = None):  # refresh period as none means never.
        self._visible_assets = assets  # None means all
        self.balance = {}  # TODO : make immutable

    async def __call__(self, rest_client):
        """
        """
        rest_client = rest_client or RestClient()
        balance_run = rest_client.balance()  # TODO pass visible_assets
        accounts = (await balance_run()).accounts  # TODO : why the extra 'accounts' level ? can we get rid of it somehow ?

        self.balance = {k: v for k, v in accounts.items() if self._visible_assets is None or k in self._visible_assets}

        return self

    # TODO : howto make display to string / repr ??

    def __getitem__(self, key):
        if self.balance is None:
            raise KeyError
        return self.balance[key]

    # TODO : maybe we should keep iter design for time dependent collections
    #     And have key addressing only for time independent collections...
    def __iter__(self):
        if self.balance is None:
            raise StopIteration
        return iter(self.balance)

    def __len__(self):
        if self.balance is None:
            return 0
        return len(self.balance)


if __name__ == '__main__':

    async def assets_retrieve_nosession():
        from aiokraken.config import load_api_keyfile
        keystruct = load_api_keyfile()
        rest = RestClient(server=Server(key=keystruct.get('key'),
                                             secret=keystruct.get('secret')))
        balance = Balance()
        await balance(rest_client=rest)
        for k, p in balance.items():
            print(f" - {k}: {p}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(assets_retrieve_nosession())

    loop.close()


