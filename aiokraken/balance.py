import asyncio
from pprint import pprint

from aiokraken.rest import RestClient, Server

from collections.abc import Mapping


class Balance(Mapping):

    def __init__(self, rest_kraken=None):  # refresh period as none means never.
        self.rest_kraken = rest_kraken or RestClient()
        self.balance = None

    async def __call__(self):
        """

        :param assets:
        :param loop_period: a falsy loop_period will prevent looping
        :return:
        """
        self.balance = (await self.rest_kraken.balance()).accounts  # TODO : whythe extra level ? can we get rid of it somehow ?
        return self

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
        balance = Balance(rest_kraken=rest)
        await balance()
        for k, p in balance.items():
            print(f" - {k}: {p}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(assets_retrieve_nosession())

    loop.close()


