import asyncio

from aiokraken.config import load_account_persist
from aiokraken.rest import RestClient, Server

from collections.abc import Mapping


class Balance(Mapping):

    def __init__(self, blacklist=None, whitelist = None):
        self._blacklist = blacklist   # NONE black list means everything forbidden. Empty list means EVERYTHING ALLOWED.
        self._whitelist = whitelist   # NONE white list means everything allowed. Empty list means NOTHNG ALLOWED.
        #TODO : a better way ?

    async def __call__(self, rest_client):
        """
        """
        rest_client = rest_client or RestClient()
        balance_run = rest_client.balance()  # TODO filter with whitelist
        self.impl = (await balance_run()).accounts  # TODO : why the extra 'accounts' level ? can we get rid of it somehow ?

        return self

    # TODO : howto make display to string / repr ??

    def __getitem__(self, key):
        if key not in self._blacklist:  # filtering on local access based on blacklist.
            return self.impl[key]
        else:
            raise KeyError(f"{key} is marked as undesired Asset and is not accessible.")

    # TODO : maybe we should keep iter design for time dependent collections (OHLC, timeseries, etc.)
    #     And have key addressing only for time independent collections (index is obvious for humans - not a cryptic timestamp)...
    def __iter__(self):
        return iter(self.impl.keys())

    def __len__(self):
        return len(self.impl)


if __name__ == '__main__':

    async def assets_retrieve_nosession():
        from aiokraken.config import load_api_keyfile
        keystruct = load_api_keyfile()
        rest = RestClient(server=Server(key=keystruct.get('key'),
                                             secret=keystruct.get('secret')))
        balance = Balance(blacklist=[])
        await balance(rest_client=rest)
        for k, p in balance.items():
            print(f" - {k}: {p}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(assets_retrieve_nosession())

    loop.close()


