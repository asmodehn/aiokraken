
from collections import Mapping

import typing

from aiokraken.model.asset import Asset


class Assets(Mapping):
    """
    A simple mapping to provide various keys for an Asset

    >>> a1 = Asset(altname= "alt1", aclass= "aclass", decimals= 8, display_decimals= 5, restname= "rest1")
    >>> a2 = Asset(altname= "alt2", aclass= "aclass", decimals= 8, display_decimals= 5, restname= "rest2")
    >>> assets_coll = Assets({
    ... a1.restname: a1,
    ... a2.restname: a2,
    ... })
    >>> assets_coll["rest1"]
    Asset(altname='alt1', aclass='aclass', decimals=8, display_decimals=5, restname='rest1')
    >>> assets_coll["alt1"]
    Asset(altname='alt1', aclass='aclass', decimals=8, display_decimals=5, restname='rest1')
    >>> assets_coll["rest2"]
    Asset(altname='alt2', aclass='aclass', decimals=8, display_decimals=5, restname='rest2')
    >>> assets_coll["alt2"]
    Asset(altname='alt2', aclass='aclass', decimals=8, display_decimals=5, restname='rest2')

    """
    def __init__(self, assets_as_dict: typing.Mapping[str, Asset]):
           self.impl = assets_as_dict

    def __repr__(self):
        return repr(self.impl)

    def __str__(self):
        return str(self.impl)

    def __contains__(self, item):
        #  We need the list of markets to validate pair string passed in the request
        return (item in self.impl or
                item in {p.altname for n, p in self.impl.items()})

    def __getitem__(self, item: str):
        #  We need the list of markets to validate pair string passed in the request
        try:
            asset = self.impl[item]
        except KeyError as ke:
            altname_map = {p.altname: p for n, p in self.impl.items()}
            if item in altname_map.keys():
                asset = altname_map[item]  # get the proper type.
            else:
                raise ke  # TODO also mention addressable via alternative names...
                # RuntimeError(f"{item} not in {[k for k in self.impl.keys()]} nor {altname_map.keys()}")

        return asset

    def __len__(self):
        return len(self.impl)

    def __iter__(self):
        return iter(self.impl)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
