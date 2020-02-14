from dataclasses import dataclass, field
from datetime import datetime, MAXYEAR
from enum import Enum

import typing
import hypothesis.strategies as st
from marshmallow import fields, post_load, pre_load

from aiokraken.rest.schemas.base import BaseSchema
from hypothesis.strategies import composite


@dataclass(frozen=True)
class KLedgerInfo:
    refid: str  # reference id
    time: str  # unix timestamp of ledger
    type: str  # type of ledger entry
    aclass: str  # asset class
    asset: str  # asset
    amount: int  # transaction amount
    fee: int  # transaction fee
    balance: int  # resulting balance
    ledger_id: typing.Optional[str] = field(default=None)  # this will be set a bit after initialization


@composite
def KLedgerInfoStrategy(draw,

                        refid= st.text(max_size=20),
                        time = st.integers(min_value=int(datetime(year=1678, month=1, day=1).timestamp()),
                                       max_value=int(datetime(year=2261, month=12, day=31).timestamp())),
                    type= st.text(max_size=8),
                    aclass= st.text(max_size=8),
                    asset= st.text(max_size=8),
                    amount= st.decimals(allow_nan=False, allow_infinity=False),
                    fee= st.decimals(allow_nan=False, allow_infinity=False),
                    balance= st.decimals(allow_nan=False, allow_infinity=False),
                    ledger_id= st.one_of(st.none(),st.text(max_size=20)),
):

    return KLedgerInfo(
        refid = draw(refid),
        time= draw(time),
        type  =draw(type),
        aclass= draw(aclass),

        asset= draw(asset),
        amount=draw(amount),
        fee=draw(fee),

        balance=draw(balance),
        ledger_id=draw(ledger_id),
    )




class KLedgerInfoSchema(BaseSchema):

    refid= fields.Str()  # reference id
    time= fields.Integer(allow_none=True)  # unix timestamp of ledger
    type= fields.Str()  # type of ledger entry
    aclass= fields.Str()  # asset class
    asset= fields.Str()  # asset
    amount= fields.Decimal(as_string=True)  # transaction amount
    fee= fields.Decimal(as_string=True)  # transaction fee
    balance= fields.Decimal(as_string=True)  # resulting balance
    ledger_id= fields.Str()

    @post_load
    def build_model(self, data, **kwargs):
        return KLedgerInfo(**data)


# TODO : we should probably have a generic dict strategy for all these...
@st.composite
def KLedgerInfoDictStrategy(draw,
                          # Here we mirror arguments for the element strategy

                           refid=st.text(max_size=20),
                           time=st.integers(min_value=int(datetime(year=1678, month=1, day=1).timestamp()),
                                       max_value=int(datetime(year=2261, month=12, day=31).timestamp())),
                           type=st.text(max_size=8),
                           aclass=st.text(max_size=8),
                           asset=st.text(max_size=8),
                           amount=st.decimals(allow_nan=False, allow_infinity=False),
                           fee=st.decimals(allow_nan=False, allow_infinity=False),
                           balance=st.decimals(allow_nan=False, allow_infinity=False),
                           ledger_id=st.one_of(st.none(), st.text(max_size=20)),
                          ):
    model = draw(KLedgerInfoStrategy(

        refid = refid,
        time= time,
        type  =type,
        aclass= aclass,

        asset= asset,
        amount=amount,
        fee=fee,

        balance=balance,
        ledger_id=ledger_id,
    ))
    schema = KLedgerInfoSchema()
    return schema.dump(model)


class KLedgersResponseSchema(BaseSchema):
    ledger = fields.Dict(keys=fields.Str(), values=fields.Nested(KLedgerInfoSchema()))
    count = fields.Integer(allow_none=False)  # we need the count to know the max offset
    # maybe not ?

    @pre_load
    def retrieve_id(self, data, many, partial):  # we must retreive the id in pre_load (before parsing to KLedgerInfoSchema
        for n in data['ledger'].keys():
            data['ledger'][n].setdefault("ledger_id", n)
        return data

    @post_load
    def build_model(self, obj, many, partial):
        # we need to return the trades AND the total count (the trade response might be partial...)
        return obj['ledger'], obj['count']  # Note we wont use any special type here for now TODO: maybe PartialPayload ?

        # TODO : dataframe for ledgers ? We have the time... we can have another (reversed) timeindexed dataframe...


if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])
