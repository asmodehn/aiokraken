from uplink import Consumer, Body, get, headers, returns, params

if __package__ is not None:
    from .schemas.payload import PayloadSchema
    from .schemas.ohlc import PairOHLCSchema
    from .schemas.time import TimeSchema
else:
    from aiokraken.rest.schemas.payload import PayloadSchema
    from aiokraken.rest.schemas.ohlc import PairOHLCSchema
    from aiokraken.rest.schemas.time import TimeSchema

@headers({
    "User-Agent": "Uplink-Sample-App"
})
class Kraken(Consumer):

    @returns.json
    @get("0/public/Time")
    def get_time(self) -> PayloadSchema(TimeSchema).__class__:
        """return the time"""

    @returns.json
    @params({'pair': 'XBTEUR'})
    @get("0/public/OHLC")
    def get_ohlc(self, **info: Body) -> PayloadSchema(PairOHLCSchema('XXBTZEUR')).__class__:
        """return ohlc"""


k = Kraken(base_url="https://api.kraken.com/")

print(k.get_ohlc())

