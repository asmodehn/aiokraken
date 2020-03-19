import random

import hypothesis.strategies as st
from aiokraken.websockets.channel import Channel

from aiokraken.websockets.schemas.ticker import TickerWSSchema


@st.composite
def st_channel(draw):

    # pick a schema at random
    slist = [
        TickerWSSchema,
    ]
    schema = slist[random.randint(0, len(slist)-1)]

    return Channel(  # TODO: refine this !
        channel_id=draw(st.integers(min_value=1)),
        channel_name=draw(st.text(min_size=5)),
        pair=draw(st.text(min_size=3, max_size=4)) + "/" + draw(st.text(min_size=3, max_size=4)),
        schema=schema()
    )


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_channel().example()))
