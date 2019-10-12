# Design
Where we explain the code structure during the developpement and evolution of aiokraken v3

There is indeed more code than required for "getting things to work".
However we go through great length to make sure our design is sound, throroughly tested, along with the kraken API.

## REST
Asynchronous (purely for optimization) HTTP requests using aiohttp.
Serialization/Deserialization using marshmallow.
Internal tests on schemas properties + integration tests using pytest-recording.

This allows record and replay of possible REST responses or error codes.

## Websockets

Following mostly the same concepts as the REST part... TODO

## Unified Interface

Goal is to organise the code around a domain model of trading concepts like Order/trades/etc, but centered on the client/user perspective.
Based on it s usage of kraken.
Hopefully over time this would come in useful if we want to interface other exchanges with similar controlled semantics...