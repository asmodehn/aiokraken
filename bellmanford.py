"""
Bellman Ford Arbitrage implementation over websocket API.
"""
from __future__ import annotations
from collections import namedtuple
from datetime import datetime
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

import networkx as nx

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
        fee = pair.fees[0].get('fee')
        # TODO : pick the right fee depending on total traded volume !
        await pmatrix(base=pair.base, quote=pair.quote, ask_price=tk.ask.price, bid_price=tk.bid.price, fee_pct=fee)

    # TODO : 2 levels :
    #  - slow updates with wide list of pairs and potential interest (no fees - small data for quick compute)
    #  - websockets with potential arbitrage (including fees - detailed data & precise compute)

    async for upd in ticker(pairs=pairs, restclient=client):
        print(f"wss ==> tick: {upd}")
        # update pricematrix
        base = upd.pairname.base
        quote = upd.pairname.quote
        fee = properpairs[upd.pairname].fees[0].get('fee')
        await pmatrix(base=base, quote=quote, ask_price=upd.ask.price, bid_price=upd.bid.price, fee_pct=fee)


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

    async def __call__(self, base: Asset, ask_price: Decimal, quote: Asset, bid_price: Decimal, fee_pct: Decimal):
        if self.assets is None:  # retrieve assets for filtering calls params, only once.
            self.assets = await client.retrieve_assets()
        async with self.wlock:  # careful with concurrent control.
            if not isinstance(base, Asset):
                base = self.assets[base].restname
            if not isinstance(quote, Asset):
                quote = self.assets[quote].restname
            # These are done with decimal, but stored as numpy floats for faster compute
            self.df[quote][base] = bid_price * ((100 - fee_pct) /100)  # bid price to get: quote_curr -- (buy_price - fee) --> base_curr
            self.df[base][quote] = ((100 - fee_pct)/100) / ask_price   # ask price to get: base_curr -- (sell_price - fee) --> quote_curr

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
        if not self.assets:
            return False
        newpm = PriceMatrix(assets=[self.assets[c] for c in self.df.columns])
        # copy all values and take -log()
        for c in self.df.columns:
            # TODO : fix this : is it on row, or columns ? which is best ??
            newpm.df[c] = np.negative(np.log(self.df[c]))
        return newpm

    def to_graph(self):
        G = nx.from_pandas_adjacency(self.df, create_using=nx.DiGraph)

        # from bokeh.io import output_file, show
        # from bokeh.plotting import figure, from_networkx
        #
        # plot = figure(title="Networkx Integration Demonstration", x_range=(-1.1, 1.1), y_range=(-1.1, 1.1),
        #               tools="", toolbar_location=None)
        #
        # graph = from_networkx(G, nx.spring_layout, scale=2, center=(0, 0))
        # plot.renderers.append(graph)
        #
        # output_file("networkx_graph.html")
        # show(plot)

        return G


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
    try:
        # observe pricematrix changes
        while True:
            # TODO : efficient TUI lib !
            # print(pmtx)

            # pricegraph = pmtx.to_graph()  # display...

            neglog = pmtx.neglog()
            if neglog:
                negcycle = bellmanford(neglog)
                if len(negcycle):
                    amnt = 1  # arbitrary starting amount
                    pred = negcycle[-1]
                    dscr = f"{amnt} {pred}"
                    for cn in reversed(negcycle[:-1]):
                        amnt = amnt * pmtx[pred][cn]
                        pred = cn
                        dscr = dscr + f" -> {amnt} {pred}"
                    print(f"ARBITRAGE POSSIBLE: {dscr}")
                # TODO : from these we can extract market making opportunities ??

                # Another way :
                # negloggraph = neglog.to_graph()
                #
                # negcycle = list()
                #
                # if nx.negative_edge_cycle(negloggraph):
                #     # find it !
                #     print("NEGATIVE CYCLE FOUND !")
                #
                #     # Now find it
                #     print(f"computing cycles... {datetime.now()}")
                #
                #     for cycle in nx.simple_cycles(negloggraph):
                #     # for cycle in nx.cycle_basis(negloggraph):  # NOT implemented !
                #         # find negative weight sum (cycle need to be more than one node)
                #         if sum(negloggraph[n][m].get('weight') for n, m in zip(cycle, cycle[1:])) < 0:
                #             print(f"Found one: {cycle}")
                #             negcycle.append(cycle)
                #     print(negcycle)
                #     print(f"computing cycles DONE ! {datetime.now()}")
            await asyncio.sleep(5)
    finally:
        # in every case cancel the background task now
        bgtsk.cancel()

    # TODO: react !


def bellmanford(pmatrix_neglog: PriceMatrix, source='ZEUR'):

    n = len(pmatrix_neglog)
    min_dist = {source: 0}
    min_pred = {}

    # Relax edges |V - 1| times
    for i in range(n - 1):  # iterations
        for v in pmatrix_neglog.df.columns:  # vertex source
            if v in min_dist.keys():  # otherwise distance infinite until we know it...
                for w in pmatrix_neglog.df.columns:  # vertex target
                     if w not in min_dist.keys() or min_dist[w] > min_dist[v] + pmatrix_neglog[v][w]:
                        min_dist[w] = min_dist[v] + pmatrix_neglog[v][w]
                        min_pred[w] = v

    # If we can still relax edges, then we have a negative cycle
    for v in pmatrix_neglog.df.columns:
        if v in min_dist.keys():  # otherwise node is not yet relevant here
            for w in pmatrix_neglog.df.columns:
                if min_dist[w] > min_dist[v] + pmatrix_neglog[v][w]:
                    # print(f"{min_dist[w]} > {min_dist[v]} + {pmatrix_neglog[v][w]}")
                    path = (w, min_pred[w])
                    while len(set(path)) == len(path):  # while no duplicates, cycle is not complete...
                        path = (*path, min_pred[path[-1]])

                    # First cycle retrieved is *likely* (?) to be the minimal one -> the only one we are interested in
                    return path[path.index(path[-1]):]

    return ()


if __name__ == '__main__':

    asyncio.run(arbiter(user_assets=["XTZ", "ETH", "XBT", "EUR"]), debug=True)
