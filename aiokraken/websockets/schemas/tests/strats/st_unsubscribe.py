import hypothesis.strategies as st
from aiokraken.websockets.schemas.unsubscribe import (
    ChannelUnsubscribeSchema, UnsubscribeSchema, ChannelUnsubscribe,
    Unsubscribe,
)

from aiokraken.websockets.schemas.subscribe import Subscription, Subscribe, SubscriptionSchema, SubscribeSchema
from aiokraken.websockets.schemas.tests.strats.st_subscribe import st_subscription

from aiokraken.websockets.schemas.ticker import TickerWS, TickerWSSchema

@st.composite
def st_unsubscribe(draw):
    return Unsubscribe(
    subscription = draw(st_subscription()),
    pair = draw(st.lists(elements=st.text())),  # TODO : use pair with proper type
    reqid = draw(st.one_of(st.none(), st.integers()))
    )


@st.composite
def st_channel_unsubscribe(draw):
    return ChannelUnsubscribe(
    channel_id = draw(st.integers()),
    reqid = draw(st.one_of(st.none(), st.integers()))
    )

@st.composite
def st_unsubscribe_dict(draw):
    model = draw(st_unsubscribe())
    schema = UnsubscribeSchema()
    return schema.dump(model)


@st.composite
def st_channel_unsubscribe_dict(draw):
    model = draw(st_channel_unsubscribe())
    schema = ChannelUnsubscribeSchema()
    return schema.dump(model)


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_unsubscribe().example()))

    for n in range(1, 10):
        print(repr(st_unsubscribe_dict().example()))

    for n in range(1, 10):
        print(repr(st_channel_unsubscribe().example()))

    for n in range(1, 10):
        print(repr(st_channel_unsubscribe_dict().example()))
