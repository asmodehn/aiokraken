
from hypothesis import strategies as st

from aiokraken.model.ledgerframe import LedgerFrame, ledgerframe
from aiokraken.rest.schemas.kledger import KLedgerInfo, KLedgerInfoStrategy, KLedgerInfoDictStrategy


@st.composite
def st_ledgerframe(draw):
    """

    :param draw:
    :return:

    """
    ledger_list = draw(st.sets(elements=KLedgerInfoStrategy(), max_size=5))  # enforcing unicity in strategy
    ledger_dict = {t.ledger_id: t for t in ledger_list}  # building dict as it would look after marshmallow parsing

    return ledgerframe(ledger_as_dict=ledger_dict).value


if __name__ == '__main__':

    for n in range(1, 10):
        print(repr(st_ledgerframe().example()))
