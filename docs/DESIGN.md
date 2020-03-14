# Design
Where we explain the code structure during the development and evolution of aiokraken v3.

There is indeed more code than required for "getting things to work".
However we go through great length to make sure our design is sound, thoroughly tested, along with the kraken API.

## REST
Asynchronous (purely for optimization) HTTP requests using aiohttp.
Serialization/Deserialization using marshmallow.
Internal tests on schemas properties + integration tests using pytest-recording

This allows record and replay of possible REST responses or error codes from the actual kraken servers

## Websockets

Following mostly the same concepts as the REST part... TODO !

## Unified Interface

Goal is to organise the code around a domain model of trading concepts like Order/trades/etc, but centered on the client/user perspective.
Based on it s usage of kraken.
Hopefully over time this would come in useful if we want to interface other exchanges with similar controlled semantics...

Concepts Identified so far (this list will be evolving) : 

Public:

- Assets: the asset/currency details
- Markets: the assetpair details
- MarketData :  a bunch of aggregated (OHLC, etc.) for a market
- more to come...

Private:

- Balance: Current user's balance.
- Ledgers: For each "account" (for an asset/currency, as in accounting, not as in "user account"), a time-indexed dataframe.
- Trades : For each "market" ie. "trade pairs", a time-indexed dataframe.
- more to come...

The main idea is to rely on just a few "formally" defined data concepts, getting inspiration from the category theory research litterature.
For example, directed containers, seems a suitable data abstraction that would allow to easily scale  and manipulate data representation in code.

Such a first concept has been identified: A time-indexed dataframe that is
- trying to be a bi-directed container, (bimonad) in time-dimension (extract past, return future) as well as in data-dimension.
- RAII : async constructor to guarantee data is filled, otherwise the usual __init__ doesnt provide this guarantee.
- iterable : `__iter__` in the past, `__aiter__` in the future
- immutable in the past only (potentially mutable in the future) - enforced only by user-side API for now...
- self-updating: calling() it with a time interval cause an update for that time interval (mutable by outside data -> relying on server data)
also accessing a time interval with [] that has not been retrieved yet, will trigger that retrieval.
- mergeable (we can get info on one pair/market and another one, and assemble them by joining, or split, vertically / column-wise)

This is the most useful concept when retrieving time-based data from the exchange (ledger, tradehistory, etc.).


Potentially other similar key concepts like this must be identified, implemented and thoroughly tested.
It would help the user to quickly get familiar with a "consistent" interface, and form sensible intuitive assumptions quickly.


## Tests
Package Internal tests are there to alleviate python limitations (stricter types, etc.) and provide a clear understanding of the behavior.
Therefore they follow the structure of the code.

External tests are usual validation tests, and therefore should follow "behavior threads".
This is quite obvious for REST request, but less so for the unified model and interface...
