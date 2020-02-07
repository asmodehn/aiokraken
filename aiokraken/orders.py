import typing
from datetime import timedelta

from aiokraken import RestClient
from aiokraken.model.assetpair import AssetPair
from aiokraken.rest.schemas.krequestorder import RequestOrder, RequestOrderFinalized
from aiokraken.rest.schemas.kopenorder import KOpenOrderModel
from aiokraken.rest.schemas.kclosedorder import KClosedOrderModel
from aiokraken.rest.schemas.ktrade import KTradeModel


class Orders:
    """ Note : This is the monad / mutable state, providing an "imperative" interface to immutable data.
        There fore it should act as a container, on the time axis... probably via the callable / iterator protocols
    """
    open: typing.Dict[str, KOpenOrderModel]  # (filtered/market related) trade history. TODO : find out when to retrieve new. how do we know about orders ??
    closed: typing.Dict[str, KClosedOrderModel]

    def __init__(self, restclient: RestClient, valid_time: timedelta = None):
        self.restclient = restclient  # we require a restclient here since all requests here are private...
        self.validtime = valid_time   # None means always valid
        # Need async call : raii is not doable here... unless we have a separate async constructor ?
        self.open = dict()
        self.closed = dict()

    def query(self):
        # TODO : interface to query order request
        raise NotImplementedError

    async def __call__(self, order: typing.Optional[RequestOrderFinalized] = None, trade_future=False):  # TODO : pass necessary parameters
        """
        This is a call mutating this object. GOAL : updating orders out of the view of the user
        (contained datastructures change by themselves, from REST calls or websockets callback...)
        """

        if order:
            # pass the order
            # TODO:
            print(" Passing order temporarily disabled : Work in progress...")
            # response = await self.restclient.addorder(order=order)

            # optionally update market data to get until we get trade confirmed
            # done via a future
            # TODO !!!

            if order.execute:  # We should get transaction ID, so we can track the open orders...
                pass
                # txid = response.get('txid')

                # txid = response.get('txid')[0]  # only one order passed by the order request

                # oo = await self.restclient.openorders()
                # print(oo)  # NOTE : We need execute = True to get anything here...
                #
                # while txid in oo:
                #     oo = await self.restclient.openorders()
                #     print(oo)  # NOTE : We need execute = True to get anything here...

                # wait for txid in trade and not in open orders any more...

                # print(f'{txid} has been filled !')

                # TODO : schedule a trades update ?? HOWTO return a future if the user wants ? or a signal ?

        # In all cases we can refresh our open/closed orders...

        # TODO : manage mutating dicts...
        new_open = (await self.restclient.openorders()())

        # open order are updated regularly
        self.open = new_open

        new_closed = (await self.restclient.closedorders()())

        # closed orders are supposed to just keep increasing
        self.closed.update(new_closed)  # TODO : manage offset somehow...

        return self


if __name__ == '__main__':
    import asyncio
    from aiokraken.rest.client import RestClient
    from aiokraken.rest.api import Server
    from aiokraken.config import load_api_keyfile

    keystruct = load_api_keyfile()

    # Client can be global: there is only one.
    rest = RestClient(server=Server(key=keystruct.get('key'),
                                    secret=keystruct.get('secret')))

    # orders data can be global
    orders = Orders(restclient=rest)

    async def orders_retrieve_nosession():
        global rest, orders
        await orders()
        print("Open:")
        for o, details in orders.open.items():
            print(f" - {o}: {details}")
        print("Closed:")
        for c, details in orders.closed.items():
            print(f" - {c}: {details}")

    loop = asyncio.get_event_loop()

    assert len(orders.open) == 0
    assert len(orders.closed) == 0

    loop.run_until_complete(orders_retrieve_nosession())
    assert len(orders.open) > 0
    assert len(orders.closed) > 0

    # REMINDER : This must remain safe for the user : do not create any orders.
    # Rely on integration tests to validate merging of data.

    loop.close()

