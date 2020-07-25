from __future__ import annotations

# This concept of channels comes directly from the Kraken API docs : https://docs.kraken.com/websockets/#message-ohlc
import asyncio
import functools
from dataclasses import dataclass, field

import typing
from types import MappingProxyType

from aiokraken.model.timeframe import KTimeFrameModel
from result import Err, Ok, Result

from aiokraken.websockets.schemas.openorders import openOrderWS, openOrderWSSchema

from aiokraken.websockets.schemas.owntrades import ownTradeWS, ownTradeWSSchema

from aiokraken.websockets.schemas.trade import TradeWS, TradeWSSchema

from aiokraken.websockets.schemas.ohlc import OHLCUpdate, OHLCUpdateSchema

from aiokraken.websockets.schemas.ticker import TickerWS, TickerWSSchema

from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.schemas.subscribe import Subscribe, Subscription

from aiokraken.rest.exceptions import AIOKrakenSchemaValidationException

from aiokraken.rest.schemas.base import BaseSchema


_ticker_schema = TickerWSSchema()
_ohlcupdate_schema = OHLCUpdateSchema()
_trade_schema = TradeWSSchema()


# TODO : maybe a way to make partial call easier ? curry decorator ?
def _public_parser(
    *, schema: BaseSchema, data: typing.Any, pair: AssetPair
):  # TODO: refine Any ??
    try:
        # - https://docs.kraken.com/websockets-beta/#message-ticker
        # - https://docs.kraken.com/websockets-beta/#message-ohlc
        # - https://docs.kraken.com/websockets-beta/#message-trade

        # also calling the parsed model to store the pair here as well...
        parsed = schema.load(data)
        # this is specific to public streams
        parsed_with_pair = parsed(pair)

        return Ok(parsed_with_pair)
    except AIOKrakenSchemaValidationException as sve:
        return Err(error=sve)


def publicchannelparser(channel_name: str):
    if channel_name == "trade":
        return functools.partial(_public_parser, schema=_trade_schema)
    elif channel_name == "ticker":
        return functools.partial(_public_parser, schema=_ticker_schema)
    elif channel_name.startswith("ohlc"):
        return functools.partial(_public_parser, schema=_ohlcupdate_schema)
    else:
        raise NotImplementedError


####  PRIVATE


_owntrades_schema = ownTradeWSSchema()
_openorders_schema = openOrderWSSchema()


def _private_parser(*, schema: BaseSchema, data: typing.Any):  # TODO : refine Any ??
    """ ownTrades Channel callable. note the name must match the channel name returned by kraken."""
    try:
        # - https://docs.kraken.com/websockets-beta/#message-ownTrades
        # - https://docs.kraken.com/websockets-beta/#message-openOrders

        # if data is a list, we parse one element at a time
        parsed = schema.load(data, many=isinstance(data, list))
        return Ok(parsed)
    except AIOKrakenSchemaValidationException as sve:
        return Err(error=sve)


def privatechannelparser(channel_name: str):
    if channel_name == "ownTrades":
        return functools.partial(_private_parser, schema=_owntrades_schema)
    elif channel_name == "openOrders":
        return functools.partial(_private_parser, schema=_openorders_schema)
    else:
        raise NotImplementedError


if __name__ == "__main__":
    raise NotImplementedError
