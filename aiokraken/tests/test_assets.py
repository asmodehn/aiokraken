# TODO : test assets with aioresponses !

import unittest
import aiohttp
from aioresponses import aioresponses

from aiokraken.assets import Assets


class TestAssets(unittest.IsolatedAsyncioTestCase):
    async def test_assets(self):
        with aioresponses() as m:
            m.get(
                "https://api.kraken.com/0/public/Assets",
                payload={
                    "error": [],
                    "result": {
                        "XETH": {
                            "aclass": "currency",
                            "altname": "ETH",
                            "decimals": 10,
                            "display_decimals": 5,
                        },

                        "XXBT": {
                            "aclass": "currency",
                            "altname": "XBT",
                            "decimals": 10,
                            "display_decimals": 5,
                        },
                    },
                },
            )

            assets = await Assets.retrieve()

        assert len(assets) == 2
        assert 'XETH' in assets.keys()
        assert 'XXBT' in assets.keys()
        assert assets['XETH'].aclass == "currency"
        assert assets['XETH'].altname == "ETH"
        assert assets['XETH'].decimals == 10
        assert assets['XETH'].display_decimals == 5

        assert assets['XXBT'].aclass == "currency"
        assert assets['XXBT'].altname == "XBT"
        assert assets['XXBT'].decimals == 10
        assert assets['XXBT'].display_decimals == 5

        # Making sure we always only keep most recent data
        with aioresponses() as m:
            m.get(
                "https://api.kraken.com/0/public/Assets",
                payload={
                    "error": [],
                    "result": {
                        "ADA": {"aclass": "currency", "altname": "ADA", "decimals": 8, "display_decimals": 6},
                        "XETH": {
                            "aclass": "currency",
                            "altname": "ETH",
                            "decimals": 10,
                            "display_decimals": 5,
                        },

                    },
                },
            )

            assets = await Assets.retrieve()

        assert len(assets) == 2
        assert 'XETH' in assets.keys()
        assert 'ADA' in assets.keys()
        assert assets['XETH'].aclass == "currency"
        assert assets['XETH'].altname == "ETH"
        assert assets['XETH'].decimals == 10
        assert assets['XETH'].display_decimals == 5

        assert assets['ADA'].aclass == "currency"
        assert assets['ADA'].altname == "ADA"
        assert assets['ADA'].decimals == 8
        assert assets['ADA'].display_decimals == 6


if __name__ == "__main__":
    import unittest
    unittest.main()
