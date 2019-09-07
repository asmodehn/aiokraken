import marshmallow
from marshmallow import fields, pre_load, post_load
from decimal import Decimal

from ..exceptions import AIOKrakenException
from ...model.time import Time


class BalanceSchema(marshmallow.Schema):
    class Meta:
        # Pass EXCLUDE as Meta option to keep marshmallow 2 behavior
        # ref: https://marshmallow.readthedocs.io/en/stable/upgrading.html#upgrading-to-3-0
        unknown = getattr(marshmallow, "EXCLUDE", None)

    # """ Schema to parse the string received"""
    # unixtime = marshmallow.fields.Int(required=True)
    # # rfc1123 ??

    ZEUR = marshmallow.fields.Decimal(default=Decimal(0.0))
    XXBT = marshmallow.fields.Decimal(default=Decimal(0.0))
    XXRP = marshmallow.fields.Decimal(default=Decimal(0.0))


    @marshmallow.pre_load(pass_many=False)
    def get_data(self, data, **kwargs):
        return data

    @marshmallow.post_load(pass_many=False)
    def make_balance(self, data, **kwargs):
        return data
        #return Time(data.get("unixtime"))

