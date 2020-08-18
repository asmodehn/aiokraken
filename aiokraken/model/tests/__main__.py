import unittest

"""
Embedded model tests, to validate knowledge representation on user installation.
uses integrated python tools only.
"""


# import your test modules
if __package__ is not None:
    from . import test_ohlc, test_ticker, test_asset, test_assetpair, test_currency, test_pair, test_time
else:
    import test_ohlc, test_ticker, test_asset, test_assetpair, test_currency, test_pair, test_time

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(test_ohlc))
suite.addTests(loader.loadTestsFromModule(test_ticker))
suite.addTests(loader.loadTestsFromModule(test_asset))
suite.addTests(loader.loadTestsFromModule(test_assetpair))
suite.addTests(loader.loadTestsFromModule(test_currency))
suite.addTests(loader.loadTestsFromModule(test_pair))
# TODO : fix time test !
#suite.addTests(loader.loadTestsFromModule(test_time))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)

if result.wasSuccessful():
    exit(0)
else:
    exit(1)
