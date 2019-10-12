import marshmallow
from marshmallow import fields, pre_load, post_load

from .base import BaseSchema

from ..exceptions import AIOKrakenException
from ...model.ticker import Ticker


class TickerSchema(BaseSchema):
    # <pair_name> = pair name
    # TODO : namedtuples with nested schema ...
    a = fields.List(fields.Number())  # ask array(<price>, <whole lot volume>, <lot volume>),
    b = fields.List(fields.Number())  #bid array(<price>, <whole lot volume>, <lot volume>),
    c = fields.List(fields.Number())  #last trade closed array(<price>, <lot volume>),
    v = fields.List(fields.Number())  #volume array(<today>, <last 24 hours>),
    p = fields.List(fields.Number())  #volume weighted average price array(<today>, <last 24 hours>),
    t = fields.List(fields.Number())  #number of trades array(<today>, <last 24 hours>),
    l = fields.List(fields.Number())  #low array(<today>, <last 24 hours>),
    h = fields.List(fields.Number())  #high array(<today>, <last 24 hours>),
    o = fields.Number()  #today's opening price



#  a runtime cache of schemas (class !) for different pairs
_pair_ticker_schemas = {}

# TODO : Change that into a class (functor) to have both a call to build instance and a item accessor for the schema/class itself...
def PairTickerSchema(pair):
    """helper function to embed OHLC data frame parsing into a field with any name...
        returns a new instance of the class, creating the class if needed
    """

    def build_model(self, data, **kwargs):
        assert len(data.get('error', [])) == 0  # Errors should have raised exception previously !
        return Ticker(b=data.get('pair').get('b'),
                      a=data.get('pair').get('a'),
                      l=data.get('pair').get('l'),
                      p=data.get('pair').get('p'),
                      h=data.get('pair').get('h'),
                      c=data.get('pair').get('c'),
                      o=data.get('pair').get('o'),
                      t=data.get('pair').get('t'),
                      v=data.get('pair').get('v'))


    try:
        return _pair_ticker_schemas[pair]()
    except KeyError:
        _pair_ticker_schemas[pair] = type(f"{pair}_TickerSchema", (BaseSchema,), {
            'pair': marshmallow.fields.Nested(TickerSchema, data_key=pair),
            'make_model': marshmallow.post_load(pass_many=False)(build_model)

        })
    finally:
        return _pair_ticker_schemas[pair]()

