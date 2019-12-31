from dataclasses import dataclass

import marshmallow
import typing
from decimal import Decimal

from marshmallow import fields, post_load, post_dump, pre_dump, pre_load
from hypothesis import strategies as st
from .base import BaseSchema, BaseOptionalSchema


@dataclass(frozen=True, init=False)
class Balance:

    accounts: typing.Dict[str, Decimal]  # TODO : str => Asset ???  Maybe one field per asset allowed/present ??

    def __init__(self, **accounts):
        object.__setattr__(self, 'accounts', {})
        for c, a in accounts.items():
            try:
                # we can cast directly to KCurrency here, schema has taken care of the aliases from kraken side.
                self.accounts[c] = Decimal(a)  # todo : change to "money" to embed currency in there...
            except Exception as e:
                raise e  # TODO : handle properly

    def __repr__(self):
        """ Unambiguous internal representation"""
        return repr([f"{c}: {a}" for c, a in self.accounts.items()])


@st.composite
def BalanceStrategy(draw, assets=st.text(min_size=1, max_size=5), amount=st.decimals(allow_nan=False, allow_infinity=False)):
    return Balance(**{ draw(assets): draw(amount)})


class BalanceSchema(BaseSchema):
    accounts = fields.Dict(keys=fields.String(), values=fields.Decimal())

    @post_dump
    def adjust_currencies(self, data, **kwargs):
        # Using aliases manually via the field to convert currencies
        # We need to output string keys for marshmallow to recognize them
        return {c: v for c, v in data['accounts'].items()}

    @pre_load
    def accounts_field(self, data, **kwargs):
        return {'accounts': data}

    @post_load
    def make_balance(self, data, **kwargs):
        # Note : data is supposed to be a dict
        assert isinstance(data, dict)
        return Balance(**data['accounts'])


@st.composite
def KDictStrategy(draw, model_strategy):
    model = draw(model_strategy)
    schema = BalanceSchema()
    return schema.dump(model)


if __name__ == "__main__":
    import pytest

    pytest.main(["-s", "--doctest-modules", "--doctest-continue-on-failure", __file__])
