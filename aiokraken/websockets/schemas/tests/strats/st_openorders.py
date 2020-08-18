import hypothesis.strategies as st
from aiokraken.websockets.schemas.openorders import (
    openOrderDescrWS, openOrderDescrWSSchema, openOrderWS, openOrderWSSchema,
)


@st.composite
def st_openorderdescrws(draw):
    return openOrderDescrWS(
        pair= draw(st.text()),
        type= draw(st.text()),
        ordertype= draw(st.text()),
        price= draw(st.floats(allow_nan=False, allow_infinity=False)),
        price2= draw(st.floats(allow_nan=False, allow_infinity=False)),
        leverage= draw(st.floats(allow_nan=False, allow_infinity=False)),
        order= draw(st.text()),
        close= draw(st.text()),
        position= draw(st.one_of(st.none(),st.text()))
    )

@st.composite
def st_openorderdescrwsdict(draw):
    model = draw(st_openorderdescrws())
    schema = openOrderDescrWSSchema()
    return schema.dump(model)

@st.composite
def st_openorderws(draw):
    return openOrderWS(
        orderid=draw(st.text()),
        refid= draw(st.text()),
        userref= draw(st.integers()),
        status= draw(st.text()),
        opentm= draw(st.floats(allow_nan=False, allow_infinity=False)),
        starttm= draw(st.floats(allow_nan=False, allow_infinity=False)),
        expiretm= draw(st.floats(allow_nan=False, allow_infinity=False)),
        descr= draw(st_openorderdescrws()),
        vol= draw(st.floats(allow_nan=False, allow_infinity=False)),
        vol_exec= draw(st.floats(allow_nan=False, allow_infinity=False)),
        cost= draw(st.floats(allow_nan=False, allow_infinity=False)),
        fee= draw(st.floats(allow_nan=False, allow_infinity=False)),
        avg_price= draw(st.floats(allow_nan=False, allow_infinity=False)),
        stopprice= draw(st.floats(allow_nan=False, allow_infinity=False)),
        limitprice= draw(st.floats(allow_nan=False, allow_infinity=False)),
        misc= draw(st.text()),
        oflags= draw(st.text()),
    )


@st.composite
def st_openorderwsdict(draw):
    model = draw(st_openorderws())
    schema = openOrderWSSchema()
    return schema.dump(model)


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_openorderdescrws().example()))

    for n in range(1, 10):
        print(repr(st_openorderdescrwsdict().example()))

    for n in range(1, 10):
        print(repr(st_openorderws().example()))

    for n in range(1, 10):
        print(repr(st_openorderwsdict().example()))
