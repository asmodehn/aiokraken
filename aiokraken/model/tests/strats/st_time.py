from aiokraken.model.time import Time
from hypothesis import strategies as st
from datetime import datetime

@st.composite
def st_time(draw):
    # generating times from EPOCH
    return Time(draw(st.datetimes(min_value=datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0))).timestamp())


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_time().example()))


