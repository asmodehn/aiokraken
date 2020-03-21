
from collections import Mapping

import typing

from aiokraken.model.asset import AssetClass

from aiokraken.model.assetpair import AssetPair


class AssetPairs(Mapping):
    """
    A simple mapping to provide various keys for an Asset

    >>> ap1 = AssetPair(
    ...         altname= "alt1", wsname="ws1", aclass_base= AssetClass.currency, base="base",
    ...         aclass_quote=AssetClass.currency.name, quote="quote", lot='1.2345',
    ...         pair_decimals=8, lot_decimals=8, lot_multiplier=2,
    ...         leverage_buy=[], leverage_sell=[], fees=[], fees_maker=[], fee_volume_currency="volc",
    ...         margin_call= 3, margin_stop= 5, restname="rest1")
    >>> ap2 = AssetPair(
    ...         altname= "alt2", wsname="ws2", aclass_base= AssetClass.currency, base="base",
    ...         aclass_quote=AssetClass.currency.name, quote="quote", lot='1.2345',
    ...         pair_decimals=8, lot_decimals=8, lot_multiplier=2,
    ...         leverage_buy=[], leverage_sell=[], fees=[], fees_maker=[], fee_volume_currency="volc",
    ...         margin_call= 3, margin_stop= 5, restname="rest2")
    >>> assetpairs_coll = AssetPairs({
    ... ap1.restname: ap1,
    ... ap2.restname: ap2,
    ... })
    >>> assetpairs_coll["rest1"]
    AssetPair(altname='alt1', wsname='ws1', aclass_base=currency, base='base', aclass_quote='currency', quote='quote', lot='1.2345', pair_decimals=8, lot_decimals=8, lot_multiplier=2, leverage_buy=[], leverage_sell=[], fees=[], fees_maker=[], fee_volume_currency='volc', margin_call=3, margin_stop=5, restname='rest1')
    >>> assetpairs_coll["alt1"]
    AssetPair(altname='alt1', wsname='ws1', aclass_base=currency, base='base', aclass_quote='currency', quote='quote', lot='1.2345', pair_decimals=8, lot_decimals=8, lot_multiplier=2, leverage_buy=[], leverage_sell=[], fees=[], fees_maker=[], fee_volume_currency='volc', margin_call=3, margin_stop=5, restname='rest1')
    >>> assetpairs_coll["rest2"]
    AssetPair(altname='alt2', wsname='ws2', aclass_base=currency, base='base', aclass_quote='currency', quote='quote', lot='1.2345', pair_decimals=8, lot_decimals=8, lot_multiplier=2, leverage_buy=[], leverage_sell=[], fees=[], fees_maker=[], fee_volume_currency='volc', margin_call=3, margin_stop=5, restname='rest2')
    >>> assetpairs_coll["alt2"]
    AssetPair(altname='alt2', wsname='ws2', aclass_base=currency, base='base', aclass_quote='currency', quote='quote', lot='1.2345', pair_decimals=8, lot_decimals=8, lot_multiplier=2, leverage_buy=[], leverage_sell=[], fees=[], fees_maker=[], fee_volume_currency='volc', margin_call=3, margin_stop=5, restname='rest2')

    """
    def __init__(self, assetpairs_as_dict: typing.Mapping[str, AssetPair]):
           self.impl = assetpairs_as_dict

    def __repr__(self):
        return repr(self.impl)

    def __str__(self):
        return str(self.impl)

    def __getitem__(self, item: str):
        #  We need the list of markets to validate pair string passed in the request
        try:
            assetpair = self.impl[item]
        except KeyError as ke:
            altname_map = {p.altname: p for n, p in self.impl.items()}
            wsname_map = {p.wsname: p for n, p in self.impl.items()}
            if item in altname_map.keys():
                assetpair = altname_map[item]  # get the proper type.
            elif item in wsname_map.keys():
                assetpair = wsname_map[item]  # get the proper type.
            else:
                raise ke  # TODO also mention addressable via alternative names...
                # RuntimeError(f"{item} not in {[k for k in self.impl.keys()]} nor {altname_map.keys()}")

        return assetpair

    def __len__(self):
        return len(self.impl)

    def __iter__(self):
        return iter(self.impl)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
