import unittest

"""
Embedded model tests, to validate knowledge representation on user installation.
uses integrated python tools only.
"""


# import your test modules
if __package__ is not None:
    from . import test_time, test_ticker, test_payload, test_ohlc, test_kabtype, test_ktm, test_krequestorder, \
        test_kordertype, test_korderdescr, test_kopenorder, test_balance, test_kasset, test_kassetpair
else:
    import test_time, test_ticker, test_payload, test_ohlc, test_kabtype, test_ktm, test_krequestorder, test_kordertype, test_korderdescr, test_kopenorder, test_balance, test_kasset, test_kassetpair

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(test_time))
suite.addTests(loader.loadTestsFromModule(test_balance))
suite.addTests(loader.loadTestsFromModule(test_kasset))
suite.addTests(loader.loadTestsFromModule(test_kassetpair))
suite.addTests(loader.loadTestsFromModule(test_ticker))
suite.addTests(loader.loadTestsFromModule(test_payload))
suite.addTests(loader.loadTestsFromModule(test_ohlc))
suite.addTests(loader.loadTestsFromModule(test_kabtype))
suite.addTests(loader.loadTestsFromModule(test_ktm))
suite.addTests(loader.loadTestsFromModule(test_krequestorder))
suite.addTests(loader.loadTestsFromModule(test_kordertype))
suite.addTests(loader.loadTestsFromModule(test_korderdescr))
suite.addTests(loader.loadTestsFromModule(test_kopenorder))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)

if result.wasSuccessful():
    exit(0)
else:
    exit(1)
