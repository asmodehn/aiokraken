import hypothesis.strategies as st
from aiokraken.websockets.schemas.owntrades import ownTradeWS, ownTradeWSSchema


@st.composite
def st_owntradews(draw):
    return ownTradeWS(
        tradeid= draw(st.text()),
        ordertxid= draw(st.text()),
        postxid= draw(st.text()),
        pair= draw(st.text()),
        time= draw(st.floats(allow_nan=False, allow_infinity=False)),
        type= draw(st.text()),
        ordertype= draw(st.text()),
        price= draw(st.floats(allow_nan=False, allow_infinity=False)),
        cost= draw(st.floats(allow_nan=False, allow_infinity=False)),
        fee= draw(st.floats(allow_nan=False, allow_infinity=False)),
        vol= draw(st.floats(allow_nan=False, allow_infinity=False)),
        margin=draw(st.floats(allow_nan=False, allow_infinity=False)),

        # seems to have been added recently (some trades dont have it, despite having a postxid...)
        posstatus=draw(st.one_of(st.text(), st.none())),
    )


@st.composite
def st_owntradewsdict(draw):
    model = draw(st_owntradews())
    schema = ownTradeWSSchema()
    return schema.dump(model)


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_owntradews().example()))

    for n in range(1, 10):
        print(repr(st_owntradewsdict().example()))

