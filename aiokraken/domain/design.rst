Design Concepts
===============

Some concepts related to code design here...
waiting for formal specification in allo, or some implementation in a stricter langauge (purescript ?).

There are two players in this trading game. The trader (player), that has *assets*, represented on the exchange with an account,
and the exchange (environment), that provides data about various *assetpairs*.

The trader wants to know the assets that he owns and their evolution over time. This is recorded in *Ledgers*.
He also needs to know the various pairs price evolution over time, given by the exchange as *OHLCV*.

To acquire an asset, an *order* must be passed for a related assetpair.
When this order is executed, a *trade* is the proof of what has happened.


fishrod
-------

Most of these data concepts here are implemented in python via a "fishrod" design:

- class instantiation indicates user interest in one specific kind of data.
- instance __call__ (async) actually performs (REST) request -> response under the hood, but returns an 'updated self'.
  *Corollary:* if this is not performed by the user , there is no active information update.
- iteration on the instance allows to browse through **old** data,
  so does __getitem__, __len__ and other potential mapping interface methods
- async iteration on the instance allows to expect **new** data and subscribe to websocket published data.
  This also updates appropriately the instance, but only the update is forwarded to the user.
  *Corollary:* if this is not performed by some coroutine on the user side, there is no passive information update.



