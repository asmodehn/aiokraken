from enum import Enum


# Some kind of ADT...
# or maybe not ? There are things ongoing in python for this already... TaggedUnion, algebraic-data-types, etc.
class StringEnum(Enum):

    def __str__(self) -> str:
        return f'{self.name}'

    def __repr__(self) -> str:
        return f'{self.name}'

    def __contains__(self, item) -> bool:
        return item in self.__members__

    # TODO. careful with hierarchies...
    # def __add__(self, other):
    #     # union
    #     return type(StringEnum)

    # TODO. careful with hierarchies...
    # def __mul__(self, other):
    #   # intersection
    #
