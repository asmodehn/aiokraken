"""
Bellman Ford Arbitrage implementation over websocket API.
"""
from __future__ import annotations
from collections import namedtuple
from decimal import Decimal
from math import log

import pandas as pd
import numpy as np
import asyncio

import typing

from aiokraken.model.assetpair import AssetPair

from aiokraken.rest import AssetPairs, Assets

from aiokraken.model.asset import Asset

from aiokraken.rest.client import RestClient
from aiokraken.websockets.publicapi import ticker

client = RestClient()


async def ticker_updates(pairs: typing.Union[AssetPairs, typing.Iterable[AssetPair]], pmatrix):
    # For required pairs, get ticket updates
    if isinstance(pairs, AssetPairs):  # TODO : we need to unify iterable of pairs somehow...
        properpairs = pairs
        pairs = [p for p in pairs.values()]
    else:
        properpairs = AssetPairs({p.wsname: p for p in pairs})

    tkrs = await client.ticker(pairs=[p for p in pairs])
    # TODO : build price matrix

    for p, tk in tkrs.items():
        # retrieve the actual pair
        pair = properpairs[p]
        await pmatrix(base=pair.base, quote=pair.quote, ask_price=tk.ask.price, bid_price=tk.bid.price)

    async for upd in ticker(pairs=pairs, restclient=client):
        print(f"wss ==> tick: {upd}")
        # update pricematrix
        base = upd.pairname.base
        quote = upd.pairname.quote
        await pmatrix(base=base, quote=quote, ask_price=upd.ask.price, bid_price=upd.bid.price)


class PriceMatrix:
    # Note This matrix is square
    # since we want to do arbitrage and find cycles...
    df: pd.DataFrame
    # we also need to be careful that only one writer can modify data at a time...
    wlock: asyncio.Lock

    assets: typing.Optional[Assets]

    def __init__(self, assets: typing.Union[Assets, typing.Iterable[Asset]]):
        self.wlock = asyncio.Lock()
        if isinstance(assets, Assets):
            assets = [a for a in assets.values()]
        self.df = pd.DataFrame(data={c.restname: {c.restname: None for c in assets} for c in assets}, columns=[c.restname for c in assets], dtype='float64')
        self.assets = None

    async def __call__(self, base: Asset, ask_price: Decimal, quote: Asset, bid_price:Decimal):
        if self.assets is None:  # retrieve assets for filtering calls params, only once.
            self.assets = await client.retrieve_assets()
        async with self.wlock:  # careful with concurrent control.
            if not isinstance(base, Asset):
                base = self.assets[base].restname
            if not isinstance(quote, Asset):
                quote = self.assets[quote].restname
            self.df[base][quote] = ask_price
            self.df[quote][base] = bid_price

    def __getitem__(self, item):
        if item not in self.df.columns:
            raise KeyError(f"{item} not found")
        if item not in self.df:
            return pd.Series(dtype=pd.dtype('decimal'))
        return self.df[item]

    def __len__(self):
        return len(self.df.columns)

    def __str__(self):
        return self.df.to_string()

    def neglog(self):
        newpm = PriceMatrix(assets=[self.assets[c] for c in self.df.columns])
        # copy all values and take -log()
        for c in self.df.columns:
            # TODO : fix this : is it on row, or columns ? which is best ??
            newpm.df[c] = np.negative(np.log(self.df[c]))
        return newpm


def test_pricematrix_mapping():
    # testing with string for simplicity for now
    pm = PriceMatrix(["EUR", "BTC"])

    pm["EUR"]["BTC"] = Decimal(1.234)
    pm["BTC"]["EUR"] = Decimal(4.321)

    assert pm["EUR"]["BTC"] == Decimal(1.234)
    assert pm["BTC"]["EUR"] == Decimal(4.321)


async def arbiter(user_assets):

    assets = await client.retrieve_assets()
    proper_userassets = Assets(assets_as_dict={assets[a].restname: assets[a] for a in user_assets})

    assetpairs = await client.retrieve_assetpairs()
    proper_userpairs = AssetPairs(assetpairs_as_dict={p.wsname:p for p in assetpairs.values()
                                                      if p.wsname is not None and (
                                                              p.base in proper_userassets or p.quote in proper_userassets
                                                      )})

    # retrieving widely related assets
    related_assets = set(assets[p.base] for p in proper_userpairs.values()) | set(assets[p.quote] for p in proper_userpairs.values())
    proper_related_assets = Assets({a.restname: a for a in related_assets})
    pmtx = PriceMatrix(assets=proper_related_assets)

    # running ticker updates in background
    bgtsk = asyncio.create_task(ticker_updates(pairs=proper_userpairs, pmatrix=pmtx))

    # observe pricematrix changes
    while True:
        # TODO : efficient TUI lib !
        print(pmtx)
        # if bellmanford(pmtx):
        #     break  # exit and stops the program
        await asyncio.sleep(5)
    # TODO: react !



# class WeightedPath:
#
#     paths:
#
#     def __init__(self, source: str):
#         self.graph = {source: 0}
#
#     # one iteration to chose a minimum path
#     def __call__(self, source, target_weights: typing.Mapping[str, float]):
#         for tw in target_weights:
#             if tw > self[source] + pmatrix_neglog[v][w]):
#                     min_dist[w] = min_dist[v] + pmatrix_neglog[v][w]
#         pass
#
#     def __getitem__(self, item):
#         # return the total minimal distance to reach this node
#
#     def __len__(self):
#         return len(self.paths)


def bellmanford(pmatrix: PriceMatrix, source='ZEUR'):

    pmatrix_neglog = pmatrix.neglog()

    n = len(pmatrix_neglog)
    min_dist = {source: (0,)}

    # Relax edges |V - 1| times
    for i in range(n - 1):  # iterations
        for v in pmatrix_neglog.df.columns:  # vertex
            for w in pmatrix_neglog.df.columns:  # vertex
                if sum(min_dist[w]) > sum(*min_dist[v], pmatrix_neglog[v][w]):
                    min_dist[w] = min_dist[v] + pmatrix_neglog[v][w]

    # If we can still relax edges, then we have a negative cycle
    for v in pmatrix_neglog.df.columns:
        for w in pmatrix_neglog.df.columns:
            if sum(min_dist[w]) > sum(*min_dist[v], pmatrix_neglog[v][w]):
                print(f"sum({min_dist[w]}) > sum(*{min_dist[v]}, {pmatrix_neglog[v][w]})")
                print(f" => {min_dist[w]}")
                return True
    return False














if __name__ == '__main__':

    asyncio.run(arbiter(user_assets=["XTZ", "ETH", "XBT", "EUR"]))
