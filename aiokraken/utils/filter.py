from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass

import typing

import dpcontracts


@dataclass
class Filter:

    """
    filter Accumulator to manage params of requests and compress actual requests...
    """

    rules: typing.Dict[typing.Any, bool]
    default: bool

    def __init__(self, whitelist=None, blacklist=None, default_allow = True):

        if whitelist:
            self.rules = {w: True for w in whitelist}
        else:
            self.rules = {}

        if blacklist:
            for f in blacklist:
                if f in self.rules:
                    self.rules.pop(f)
                else:
                    self.rules[f] = False

        self.default = default_allow

    @property
    def whitelist(self):
        return [e for e in self.rules if self.rules[e]]

    @property
    def blacklist(self):
        return [e for e in self.rules if not self.rules[e]]

    @dpcontracts.require("Filters must have the same default behavior", lambda args: args.other.default == args.self.default)
    def __add__(self, other: Filter):
        # immutable behavior...
        return Filter(whitelist=self.whitelist + other.whitelist, blacklist=self.blacklist + other.blacklist, default_allow= self.default)

    # Not sure __sub__ makes any semantic sense here


if __name__ == '__main__':

    f = Filter(whitelist=['A', 'B', 'C'], blacklist=['Z', 'Y'])

    assert f.whitelist == ['A', 'B', 'C']

    assert f.blacklist == ['Z', 'Y']

    g = Filter(whitelist=['D'], blacklist=['X'])

    assert f + g == Filter(whitelist=['A', 'B', 'C', 'D'], blacklist=['Z', 'Y', 'X'])
