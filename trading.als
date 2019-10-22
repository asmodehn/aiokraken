sig Market {
	//pair: String  // TODO
	marketprice: one Int
}{
	marketprice > 0
}

abstract sig Order {
	market: one Market,
}

abstract sig SellOrder, BuyOrder extends Order {}
fact { SellOrder + BuyOrder = Order }

sig LimitSell extends SellOrder { limitprice: Int }
sig LimitBuy extends BuyOrder { limitprice: Int }

sig MarketSell extends SellOrder {}
sig MarketBuy extends BuyOrder {}
fact { LimitSell + MarketSell = SellOrder }
fact { LimitBuy + MarketBuy = BuyOrder }

pred example {}

run example for exactly 2 Market, 5 Order
