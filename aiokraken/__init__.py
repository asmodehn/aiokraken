""" Kraken main module """
from .websockets.client import WssClient
from .rest.client import RestClient

"""
aiokraken as a library...
Note : importing the model subpackage would trigger sideeffects (code execution, etc.)
which is not an expected behavior of a library.


Design notes : 
- a user's strategy can be applied to multiple pairs (with levels and values relative to the pair)
 => So it s not "each market has its strategy, and markets evolve by trying different strategies...".
    It s more "Each strategy is applicable to some markets, and strategies can evolve..."
    In this context "evolves" means is created, lives and then finally dies. Then another is created, etc.
 => No evolution on the markets. Evolution on strategies to adapt to the market current situation. Strategy get into, or withdraw from markets.
 => Default way of Expressing a strategy must be market agnostic.
 => high level concepts needed in library user API.
"""



