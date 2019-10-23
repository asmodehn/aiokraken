from dataclasses import dataclass

import marshmallow
import typing
from marshmallow import fields, pre_load, post_load
from decimal import Decimal

from aiokraken.rest.schemas.kcurrency import KCurrency
from .base import BaseOptionalSchema
from ..exceptions import AIOKrakenException
from ...model.time import Time

@dataclass(frozen=True, init=False)
class Balance:

    accounts: typing.Dict[KCurrency, Decimal]

    def __init__(self, **accounts):
        object.__setattr__(self, 'accounts', {})
        for c, a in accounts.items():
            try:
                self.accounts[KCurrency(c)] = Decimal(a)  # todo : change to "money" to embed currency in there...
            except Exception as e:
                raise e  # TODO : handle properly

    def __repr__(self):
        """ Unambiguous internal representation"""
        return repr([f"{c}: {a}" for c, a in self.accounts.items()])


# Generating a Balance Schema dynamically from the set of known currencies
# Unknown currencies are simply ignored.
def _balance_schema_helper():
    """helper function to create balance schemas from the KCurrency enum
    """

    def make_balance(self, data, **kwargs):
        # Note : data is supposed to be a dict
        assert isinstance(data, dict)
        return Balance(**data)

    # build fields
    fields_dict = {}
    for _, c in KCurrency.__members__.items():
        # CAREFUL : we want the kraken valid string as field name
        fields_dict.setdefault(c.value, marshmallow.fields.Decimal(default=Decimal(0.0)))

    fields_dict.update({'make_balance': marshmallow.post_load(pass_many=False)(make_balance)})

    return type(f"BalanceSchema", (BaseOptionalSchema, ), fields_dict)


BalanceSchema = _balance_schema_helper()
