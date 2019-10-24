from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field
from .pair import Pair

#
# class Order:
#     def __init__(self,  pair, volume, leverage = None, relative_starttm = 0, relative_expiretm = 0, fee_currency_base=True, market_price_protection=True, userref = None, execute=False, close= None):
#         # Note we probably want to minimize data stored here, if it matches default behavior on kraken, in order to side step potential formatting issues...
#         self.pair = pair
#         self.volume = volume
#         if leverage:  # this is optional member...
#             self.leverage = leverage
#
#         if relative_starttm > 0:
#             self.starttm = '+' + str(relative_starttm)
#         if relative_expiretm > 0:
#             self.expiretm = '+' + str(relative_expiretm)
#
#         # using default if nothing explicitely asked for
#         if False:  # TMP : oflags via params ?
#             self.oflags = [
#                 'fcib' if fee_currency_base else 'fciq'
#             ]  # WARNING : oflags formatting used to cause "InvalidkeyError" from the exchange...
#             # TODO : address this...
#         if not market_price_protection:
#             self.oflags.append('nompp')
#
#         if not execute:
#             self.validate = True
#         if userref:  # this is optional member
#             self.userref = userref
#         if close:
#             self.close = close
#
#     def __repr__(self):
#         # TODO : find better / cleaner way ?
#         return f"Order: pair: {self.pair} volume: {self.volume}"
#
#
# # Declaring intent via functions
#
# def bid(order: Order):
#     order.type = 'buy'
#     return order
#
#
# buy = bid
#
#
# def ask(order: Order):
#     order.type = 'sell'
#     return order
#
#
# sell = ask
#
#
# def cancel(order: Order):
#     return order.txid
#
#
# # TODO : have some confirmation call that produce a trade...
#
#
#
#
#
# if __name__ == '__main__':
#
#     order = ask(LimitOrder(
#         pair='XBTEUR',
#         volume='3',
#         limit_price=342342,
#         close=bid(MarketOrder(
#             pair='XBTEUR',
#             volume='1'
#         ))
#     ))
#     print(order)




