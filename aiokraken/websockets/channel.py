from __future__ import annotations

# This concept of channels comes directly from the Kraken API docs : https://docs.kraken.com/websockets/#message-ohlc
import asyncio
from dataclasses import dataclass, field

import typing

from result import Err, Ok, Result

from aiokraken.websockets.schemas.openorders import openOrderWS, openOrderWSSchema

from aiokraken.websockets.schemas.owntrades import ownTradeWS, ownTradeWSSchema

from aiokraken.websockets.schemas.trade import TradeWS, TradeWSSchema

from aiokraken.websockets.schemas.ohlc import OHLCUpdate, OHLCUpdateSchema

from aiokraken.websockets.schemas.ticker import TickerWS, TickerWSSchema

from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.schemas.subscribe import Subscribe

from aiokraken.rest.exceptions import AIOKrakenSchemaValidationException

from aiokraken.rest.schemas.base import BaseSchema


PairChannelId = typing.NamedTuple("PairChannelId", [("pair", AssetPair), ("channel_id", int)])


@dataclass(frozen=True, init=True)
class PublicChannel:
    channel_name: str
    schema: BaseSchema

    # This is the entire set of pairs known by aiokraken process for this channel.
    pairs_channel_ids: typing.Set[PairChannelId] = field(default_factory=set)
    # TODO : maybe review this as a mapping (simpler to deal with...)

    @property
    def pairs(self):
        return set(p for p, cid in self.pairs_channel_ids)

    @property
    def channel_ids(self):
        return set(cid for p, cid in self.pairs_channel_ids)

    def __or__(self, other: PublicChannel):
        assert other.channel_name == self.channel_name
        assert other.schema == self.schema
        # Joining channels
        return PublicChannel(
            pairs_channel_ids=self.pairs_channel_ids | other.pairs_channel_ids,
            channel_name= self.channel_name,
            schema=self.schema,
        )

    def __getitem__(self, item: typing.Union[AssetPair, typing.List[AssetPair]]):
        if not isinstance(item, typing.Iterable):
            item = [item]
        # splitting channels
        pcids = {pcid for pcid in self.pairs_channel_ids if pcid in item}
        if pcids:
            # TODO : maybe we dont want a clea new channel,
            #  but instead a "filtered channel set on top of the "same and unique pair-id mapping" ?
            return PublicChannel(
                pairs_channel_ids=pcids,
                channel_name=self.channel_name,
                schema=self.schema
            )
        else:
            raise KeyError(f"{item} not found in {self.pairs}")

    def __setitem__(self, key: AssetPair, value: int):
        # setting channel id on subscribed message

        for pcid in self.pairs_channel_ids:
            if pcid.pair == key:
                assert pcid.channel_id == value  # make sure the channel doesnt change id along the way
        # TODO : maybe review this depending on the usage we have of the pair-id mapping...
        self.pairs_channel_ids.add(PairChannelId(pair=key, channel_id=value))

    def __call__(self, chan_id, data, channel, pair) -> Result[typing.Union[TickerWS, OHLCUpdate, TradeWS]]:

        # structure of a message on a public channel :
        # - https://docs.kraken.com/websockets-beta/#message-ticker
        # - https://docs.kraken.com/websockets-beta/#message-ohlc
        # - https://docs.kraken.com/websockets-beta/#message-trade
        # - https://docs.kraken.com/websockets-beta/#message-spread
        # - https://docs.kraken.com/websockets-beta/#message-book

        if chan_id in self.channel_ids and pair in self.pairs:

            if channel == self.channel_name:
                # also calling the parsed model to store the pair here as well...
                parsed = self.schema.load(data)
                # this is specific to public streams
                parsed_with_pair = parsed(pair)

                return Ok(parsed_with_pair)
        return Err(error="")


@dataclass(frozen=True)
class PrivateChannel:
    """
    A channel, called when a message is received.
    Behaves as a stream, enqueueing messages until iteration is performed to consume them.

    Note : this can assemble a set of kraken channel ids in order to linearize their messages
     in only one async generator, based on subscription request.
    """

    channel_name: str
    schema: BaseSchema

    def __call__(self, data, channel) -> Result[typing.Union[ownTradeWS, openOrderWS]]:

        # structure of a message on a private channel:
        # - https://docs.kraken.com/websockets-beta/#message-ownTrades
        # - https://docs.kraken.com/websockets-beta/#message-openOrders

        if channel == self.channel_name:
            # if data is a list, we parse one element at a time
            parsed = self.schema.load(data, many=isinstance(data, list))
            return Ok(parsed)
        return Err(error="")


_ticker_schema = TickerWSSchema()
_ohlcupdate_schema = OHLCUpdateSchema()
_trade_schema = TradeWSSchema()
_owntrades_schema = ownTradeWSSchema()
_openorders_schema = openOrderWSSchema()


def channel(name: str):
    """ Create channel instances to manage streams of data from a kraken publisher.
    """
    if name == "ticker":
        chan = PublicChannel(channel_name=name,
                             schema=_ticker_schema)

    elif name.startswith("ohlc"):  # name depends also on interval !
        chan = PublicChannel(channel_name=name,
                             schema=_ohlcupdate_schema)

    elif name.startswith("trade"):
        chan = PublicChannel(channel_name=name,
                             schema=_trade_schema)

    elif name.startswith("ownTrades"):
        chan = PrivateChannel(channel_name=name,
                              schema=_owntrades_schema)

    elif name.startswith("openOrders"):
        chan = PrivateChannel(channel_name=name,
                              schema = _openorders_schema)

    else:
        raise NotImplementedError(f"Unknown channel name '{name}'. please add it to the code...")

    return chan


if __name__ == '__main__':
    raise NotImplementedError