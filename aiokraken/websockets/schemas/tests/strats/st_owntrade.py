import hypothesis.strategies as st
from aiokraken.websockets.schemas.owntrades import ownTradeWS, ownTradeWSContentSchema, ownTradeWSSchema


@st.composite
def st_owntradews(draw):
    return ownTradeWS(
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
    schema = ownTradeWSContentSchema()
    return schema.dump(model)

@st.composite
def st_owntradewspayload(draw):

    schema = ownTradeWSSchema()

    # just here to format data
    # TODO : review this, should we handle idiotic kraken format here or in channel ?
    #  Or maybe have a special "payload" or "IdDict" concept (often used with json style data)?
    obj = schema.load({
        draw(st.text()): draw(st_owntradews())
    })
    return schema.dump(obj)


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_owntradews().example()))

    for n in range(1, 10):
        print(repr(st_owntradewsdict().example()))

    for n in range(1, 10):
        print(repr(st_owntradewspayload().example()))
