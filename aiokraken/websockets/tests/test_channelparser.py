import unittest

from aiokraken.websockets.schemas.openorders import openOrderWS, openOrderWSSchema

from aiokraken.websockets.schemas.owntrades import ownTradeWS, ownTradeWSSchema


from aiokraken.websockets.schemas.ohlc import OHLCUpdate, OHLCUpdateSchema

from aiokraken.websockets.schemas.ticker import TickerWS, TickerWSSchema


from aiokraken.model.tests.strats.st_assetpair import AssetPairStrategy

from aiokraken.websockets.schemas.trade import TradeWS, TradeWSSchema

from hypothesis import given

from aiokraken.websockets.channelparser import privatechannelparser, publicchannelparser


class TestPublicChannelParser(unittest.TestCase):

    @given(trade_data=TradeWSSchema.strategy(), pair=AssetPairStrategy())
    def test_trade_parser(self, trade_data, pair):
        parse = publicchannelparser("trade")

        # https://docs.kraken.com/websockets-beta/#message-trade
        # CAREFUL here we need to pass only a list of values for the data, no keys.
        raw=[v for v in trade_data.values()]  # TODO : post dump ??
        parsed = parse(data=raw, pair=pair)

        assert parsed
        assert isinstance(parsed.value, TradeWS)

    @given(ticker_data=TickerWSSchema.strategy(), pair=AssetPairStrategy())
    def test_ticker_parser(self, ticker_data, pair):
        parse = publicchannelparser("ticker")

        # https://docs.kraken.com/websockets-beta/#message-ticker
        # CAREFUL here we need to pass a mapping of list for the data.
        raw={k: [vv for vv in v] for k, v in ticker_data.items()}  # TODO : post dump ??
        parsed = parse(data=raw, pair=pair)

        assert parsed
        assert isinstance(parsed.value, TickerWS)

    @given(ohlc_data=OHLCUpdateSchema.strategy(), pair=AssetPairStrategy())
    def test_ohlc_parser(self, ohlc_data, pair):
        parse = publicchannelparser("ohlc")

        # https://docs.kraken.com/websockets-beta/#message-ohlc
        # CAREFUL here we need to pass only a list of values for the data, no keys.
        raw=[v for v in ohlc_data.values()]  # TODO : post dump ??
        parsed = parse(data=raw, pair=pair)

        assert parsed
        assert isinstance(parsed.value, OHLCUpdate)


class TestPrivateChannelParser(unittest.TestCase):

    @given(owntrades_data=ownTradeWSSchema.strategy())
    def test_ownTrades_parser(self, owntrades_data):
        parse = privatechannelparser("ownTrades")

        # https://docs.kraken.com/websockets-beta/#message-ownTrades
        # CAREFUL here we need to pass a mapping of the data.
        raw = owntrades_data
        parsed = parse(data=raw)

        assert parsed
        assert isinstance(parsed.value, ownTradeWS)

    @given(openorders_data=openOrderWSSchema.strategy())
    def test_openOrders_parser(self, openorders_data):
        parse = privatechannelparser("openOrders")

        # https://docs.kraken.com/websockets-beta/#message-openOrders
        # CAREFUL here we need to pass only a mapping the data.
        raw= openorders_data
        parsed = parse(data=raw)

        assert parsed.ok()
        assert isinstance(parsed.value, openOrderWS)


if __name__ == '__main__':
    unittest.main()
