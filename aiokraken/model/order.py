

class Order:
    def __init__(self,  pair, volume, leverage = None, relative_starttm = 0, relative_expiretm = 0, fee_currency_base=True, market_price_protection=True, userref = None, execute=False, close= None):

        self.pair = pair
        self.volume = volume
        if leverage: # this is optional member...
            self.leverage = leverage

        self.starttm = '+' + str(relative_starttm) if relative_starttm > 0 else '0'
        self.expiretm = '+' + str(relative_expiretm) if relative_expiretm > 0 else '0'

        self.oflags = [
            'fcib' if fee_currency_base else 'fciq'
        ]
        if not market_price_protection:
            self.oflags.append('nompp')

        self.validate = not execute
        if userref:  # this is optional member
            self.userref = userref

        self.close = close

    def __repr__(self):
        # TODO : find better / cleaner way ?
        return f"Order: pair: {self.pair} volume: {self.volume} close: {repr(self.close)}"



class MarketOrder(Order):

    def __init__(self, **kwargs):
        self.ordertype='market'
        super(MarketOrder, self).__init__(**kwargs)


class LimitOrder(Order):

    def __init__(self, limit_price, **kwargs):
        self.ordertype='limit'
        self.price = limit_price
        super(LimitOrder, self).__init__(**kwargs)


class StopLossOrder(Order):

    def __init__(self, stop_loss_price, **kwargs):
        self.ordertype='stop-loss'
        self.price = stop_loss_price
        super(StopLossOrder, self).__init__(**kwargs)


class TakeProfitOrder(Order):

    def __init__(self, take_profit_price, **kwargs):
        self.ordertype='take-profit'
        self.price = take_profit_price
        super(TakeProfitOrder, self).__init__(**kwargs)


class StopLossProfitOrder(Order):

    def __init__(self, stop_loss_price, take_profit_price, **kwargs):
        self.ordertype='stop-loss-profit'
        self.price = stop_loss_price
        self.price2 = take_profit_price
        super(StopLossProfitOrder, self).__init__(**kwargs)


class StopLossProfitLimitOrder(Order):

    def __init__(self, stop_loss_price, take_profit_price, **kwargs):
        self.ordertype='stop-loss-profit-limit'
        self.price = stop_loss_price
        self.price2 = take_profit_price
        super(StopLossProfitLimitOrder, self).__init__(**kwargs)


class StopLossLimitOrder(Order):

    def __init__(self, stop_loss_trigger_price, triggered_limit_price, **kwargs):
        self.ordertype='stop-loss-limit'
        self.price = stop_loss_trigger_price
        self.price2 = triggered_limit_price
        super(StopLossLimitOrder, self).__init__(**kwargs)


class TakeProfitLimit(Order):

    def __init__(self, take_profit_trigger_price, triggered_limit_price, **kwargs):
        self.ordertype='take-profit-limit'
        self.price = take_profit_trigger_price
        self.price2 = triggered_limit_price
        super(TakeProfitLimit, self).__init__(**kwargs)


class TrailingStopOrder(Order):

    def __init__(self, trailing_stop_offset, **kwargs):
        self.ordertype='trailing-stop'
        self.price = trailing_stop_offset
        super(TrailingStopOrder, self).__init__(**kwargs)


class TrailingStopLimit(Order):

    def __init__(self, trailing_stop_offset, triggered_limit_offset, **kwargs):
        self.ordertype='trailing-stop-limit'
        self.price = trailing_stop_offset
        self.price2 = triggered_limit_offset
        super(TrailingStopLimit, self).__init__(**kwargs)


class StopLossAndLimitOrder(Order):
    def __init__(self, stop_loss_price, limit_price, **kwargs):
        self.ordertype='stop-loss-and-limit'
        self.price = stop_loss_price
        self.price2 = limit_price
        super(StopLossAndLimitOrder, self).__init__(**kwargs)


class SettlePositionOrder(Order):
    def __init__(self, **kwargs):
        self.ordertype='settle-position'
        super(SettlePositionOrder, self).__init__(**kwargs)


# Declaring intent via functions

def bid(order: Order):
    order.type = 'buy'
    return order


buy = bid


def ask(order: Order):
    order.type = 'sell'
    return order


sell = ask


def cancel(order: Order):
    return order.txid


# TODO : have some confirmation call that produce a trade...



if __name__ == '__main__':

    order = ask(LimitOrder(
        pair='XBTEUR',
        volume='3',
        limit_price=342342,
        close=bid(MarketOrder(
            pair='XBTEUR',
            volume='1'
        ))
    ))
    print(order)




