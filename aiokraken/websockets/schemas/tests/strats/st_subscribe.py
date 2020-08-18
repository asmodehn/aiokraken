import hypothesis.strategies as st
from aiokraken.websockets.schemas.subscribe import Subscription, Subscribe, SubscriptionSchema, SubscribeSchema

from aiokraken.websockets.schemas.ticker import TickerWS, TickerWSSchema

@st.composite
def st_subscription(draw):
    return Subscription(
    name = draw(st.text()),
    depth = draw(st.integers()),
    interval = draw(st.integers()),
    token = draw(st.text())
    )


@st.composite
def st_subscribe(draw):
    return Subscribe(
    subscription = draw(st_subscription()),
    pair = draw(st.lists(elements=st.text())),  # TODO : use pair with proper type
    reqid = draw(st.one_of(st.none(), st.integers()))
    )


@st.composite
def st_subscription_dict(draw):
    model = draw(st_subscription())
    schema = SubscriptionSchema()
    return schema.dump(model)


@st.composite
def st_subscribe_dict(draw):
    model = draw(st_subscribe())
    schema = SubscribeSchema()
    return schema.dump(model)


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_subscription().example()))

    for n in range(1, 10):
        print(repr(st_subscribe().example()))

    for n in range(1, 10):
        print(repr(st_subscription_dict().example()))

    for n in range(1, 10):
        print(repr(st_subscribe_dict().example()))
