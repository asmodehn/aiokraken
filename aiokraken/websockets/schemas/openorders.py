from marshmallow import fields, post_load, pre_load

from aiokraken.rest.schemas.base import BaseSchema

# https://www.kraken.com/features/websocket-api#message-openOrders

from collections import namedtuple
from dataclasses import dataclass, field, asdict
from decimal import Decimal

import typing


""" A common data structure for an openOrder """

@dataclass(frozen=True, init=True)
class openOrderDescrWS:
    pair: str           #  	string 	asset pair
    type: str           # 	string 	type of order (buy/sell)
    ordertype: str      # 	string 	order type
    price: float        # 	float 	primary price
    price2: float       # 	float 	secondary price
    leverage: float     # 	float 	amount of leverage
    order: str          # 	string 	order description
    close: str          # 	string 	conditional close order description (if conditional close set)
    position: typing.Optional[str] = field(default=None)       # 	string 	Optional - position ID (if applicable)



@dataclass(frozen=True, init=True)
class openOrderWS:

    refid: str          # 	string 	Referral order transaction id that created this order
    userref: str        # 	integer 	user reference ID
    status: str         # 	string 	status of order:
    opentm: float       # 	float 	unix timestamp of when order was placed
    starttm: float      # 	float 	unix timestamp of order start time (if set)
    expiretm: float     # 	float 	unix timestamp of order end time (if set)
    descr: openOrderDescrWS  # 	object 	order description info
    vol: float          # 	float 	volume of order (base currency unless viqc set in oflags)
    vol_exec: float     # 	float 	total volume executed so far (base currency unless viqc set in oflags)
    cost: float         # 	float 	total cost (quote currency unless unless viqc set in oflags)
    fee: float          # 	float 	total fee (quote currency)
    avg_price: float    # 	float 	average price (cumulative; quote currency unless viqc set in oflags)
    stopprice: float    # 	float 	stop price (quote currency, for trailing stops)
    limitprice: float   # 	float 	triggered limit price (quote currency, when limit based order type triggered)
    misc: str           # 	string 	comma delimited list of miscellaneous info: stopped=triggered by stop price, touched=triggered by touch price, liquidation=liquidation, partial=partial fill
    oflags: str         # 	string 	Optional - comma delimited list of order flags. viqc = volume in quote currency (not currently available), fcib = prefer fee in base currency, fciq = prefer fee in quote currency, nompp = no market price protection, post = post only order (available when ordertype = limit)

    orderid: typing.Optional[str] = field(default=None)  # this will be set a bit after initialization

    def __call__(self, orderid):
        newdata = asdict(self)
        newdata.update({'orderid': orderid})
        return openOrderWS(**newdata)

    # @staticmethod
    # def strategy(self):
    #     from aiokraken.websockets.schemas.tests.strats.st_trade import st_tradews
    #     return st_tradews()



class openOrderDescrWSSchema(BaseSchema):
    pair=fields.Str()       # 	string 	asset pair
    position=fields.Str()   # 	string 	Optional - position ID (if applicable)
    type=fields.Str()       # 	string 	type of order (buy/sell)
    ordertype=fields.Str()  # 	string 	order type
    price=fields.Float()    # 	float 	primary price
    price2=fields.Float()   # 	float 	secondary price
    leverage=fields.Float(allow_none=True) # 	float 	amount of leverage
    order=fields.Str()      # 	string 	order description
    close=fields.Str(allow_none=True)      # 	string 	conditional close order description (if conditional close set)

    @pre_load
    def cleanup(self, data, **kwargs):
        return data

    @post_load
    def build_model(self, data, **kwargs):
        return openOrderDescrWS(**data)


class openOrderWSContentSchema(BaseSchema):
    # <pair_name> = pair name

    refid=fields.Str(allow_none=True)      # 	string 	Referral order transaction id that created this order
    userref=fields.Int()    # 	integer 	user reference ID
    status=fields.Str()     # 	string 	status of order:
    opentm=fields.Float()   # 	float 	unix timestamp of when order was placed
    starttm=fields.Float(allow_none=True)  # 	float 	unix timestamp of order start time (if set)
    expiretm=fields.Float(allow_none=True) # 	float 	unix timestamp of order end time (if set)
    descr=fields.Nested(openOrderDescrWSSchema())  # 	object 	order description info

    vol=fields.Float()      # 	float 	volume of order (base currency unless viqc set in oflags)
    vol_exec=fields.Float() # 	float 	total volume executed so far (base currency unless viqc set in oflags)
    cost=fields.Float()     # 	float 	total cost (quote currency unless unless viqc set in oflags)
    fee=fields.Float()      # 	float 	total fee (quote currency)
    avg_price=fields.Float()# 	float 	average price (cumulative; quote currency unless viqc set in oflags)
    stopprice=fields.Float()# 	float 	stop price (quote currency, for trailing stops)
    limitprice=fields.Float()# 	float 	triggered limit price (quote currency, when limit based order type triggered)
    misc=fields.Str()        # 	string 	comma delimited list of miscellaneous info: stopped=triggered by stop price, touched=triggered by touch price, liquidation=liquidation, partial=partial fill
    oflags=fields.Str()     # 	string 	Optional - comma delimited list of order flags. viqc = volume in quote currency (not currently available), fcib = prefer fee in base currency, fciq = prefer fee in quote currency, nompp = no market price protection, post = post only order (available when ordertype = limit)


    @pre_load
    def cleanup(self, data, **kwargs):
        return data

    @post_load
    def build_model(self, data, **kwargs):
        return openOrderWS(**data)

    # @staticmethod
    # def strategy():
    #     from aiokraken.websockets.schemas.tests.strats.st_trade import st_tradewsdict
    #     return st_tradewsdict()


class openOrderWSSchema(BaseSchema):

    order_id = fields.Str()
    order_details = fields.Nested(openOrderWSContentSchema())

    @pre_load
    def cleanup(self, data, many, **kwargs):
        assert len(data) == 1  # only one trade here
        # temporary structure to manage kraken dynamic dict style...
        k, v = next(iter(data.items()))
        return {'order_id': k,
                'order_details': v}

    @post_load
    def build_model(self, data, many, **kwargs):
        return data['order_details'](data['order_id'])
