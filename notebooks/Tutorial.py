# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.1
#   kernelspec:
#     display_name: aiokraken
#     language: python
#     name: aiokraken
# ---

import aiokraken

# # Assets and AssetPairs
#
# This data can be retrieved from the kraken server

restclient = aiokraken.RestClient()
assets = await aiokraken.assets(restclient=restclient)
assetpairs = await aiokraken.assetpairs(restclient=restclient)

# We can retrieve the OHLC for a pair, simply via using one of its names

ohlc = await aiokraken.ohlc("XBT/EUR")  # or XXBTZEUR

# We can display a candle graph for this data

# +
from bokeh.plotting import figure, show
from bokeh.io import output_notebook
output_notebook()

from aiokraken.model.bokeh_figs.fig_ohlc import fig_ohlc
p = fig_ohlc(df=ohlc.model.dataframe)
show(p)
