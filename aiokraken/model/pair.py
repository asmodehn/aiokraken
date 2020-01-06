from dataclasses import dataclass

from aiokraken.model.currency import KCurrency


@dataclass(frozen=True)
class PairModel:
    """
    >>> p=PairModel(base=KCurrency("XBT"), quote=KCurrency("EUR"))
    >>> p.base
    XBT
    >>> p.quote
    EUR
    """

    base: KCurrency
    quote: KCurrency

    # def __post_init__(self):
    #     if self.base == self.quote:
    #         raise ValueError(f"Pair cannot have base {self.base} and quote {self.quote}")

    def __repr__(self):
        return f"{repr(self.base)}/{repr(self.quote)}"

    def __str__(self):
        # or using .value ?? see other stringenums like ordertype...
        return f"{self.base}{self.quote}"
