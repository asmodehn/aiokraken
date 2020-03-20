""" Kraken main module """
from aiokraken.rest.client import RestClient
from aiokraken.websockets.client import WssClient

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
 
Architecture note :
- Everything in model/ is supposed to be immutable / functional in usage
- Everything in the root package directory, should be "pythonic" in its usage. 
For example aiokraken.model.OHLC is immutable, but provides a stitch function returning a new instance of itself.
 And aiokraken.OHLC is immutable *by the user*, but it is mutated under the hood by aiokraken itself, without any action required from the user.
 
- Public (Assets,Markets, OHLC, etc.) / Private (Account, etc.) interfaces are separated. refer to the documentation to find out which one needs api key.
- Public interface do not need a client, one can be created automatically. PRivate interface needs a client that has been configured wiht your api key
 
- aiokraken.* are modules that should be usable from a repl (hence using ipython in main). Goal is ease of use of that level, to encourage usage and maintenance by possible newcomers.
- aiokraken is supposed to be interractive, yet very simple. The minimum is considered to be a REPL + graph display (with potential graph in terminal for tiling guis...).
When the interface is more stable, more advanced graphical GUIs can be created on top.
"""


from .assets import Assets, assets
from .markets import Markets, markets
from .ohlc import OHLC, ohlc
from .balance import Balance, balance
