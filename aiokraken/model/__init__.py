"""
These models are here to structure data and computation.
Think of it as a domain (kraken) model, formalized as classes.
The goal here is to get to Aglebraic types with what python allows...

We will put concepts that are common in both REST and WebSockets interface.
We will extend these concept very slightly, to be more "client-centric", even if the server might not provide any representation for them.
They might be useful to a user to track important metrics (such as a position even when there was no leverage to track profit for instance)
We should also strive to make impossible state non-representable, and attempt to make the upgrade path nicer for developers (by hiding datamodel behind functions for example).

Yet we will remain "Kraken-specific" and will not concern ourselves with other exchanges (including in naming).
This is therefore an attempt to reverse engineer internal state from visible API data, and extend that with useful fonctionality, for devs and for client's perspective


Regarding Domain Design in CryptoTrading (also probably valid for forex):
- Currency and Asset are two different concepts, yet intricately related in this specific type of trading.
- Asset is what you have in your balance, what you can buy and sell.
  => Data model. We need to gather all data, even potentially unknown ones, and we must enable 'experimentation' on it.
- Currency is the mean through which you buy/sell asset, and it influences the price.
  => Domain model, helpful to make computations. In the data model it might not always be present, often it can be implicit.
"""


# We need a concept of assets

# We need currencies (is related to, but might also be different from, assets)

# We need a concept of AssetPair and tradable ones (same or different ?)

# we need a concept of prices ( as a decimal number with a certain precision and a currency...)

# we need a concept for volume ( as a decimal quantity with a unit ... )

# we need a concept for each of the possible orders (different semantic for each)

# we need a concept for trades

# we need a concept for  positions (leverage or not - extending slightly kraken model)
