import unittest

"""
Embedded model tests, to validate knowledge representation on user installation.
uses integrated python tools only.
"""


# import your test modules
if __package__ is not None:
    from . import test_time, test_ohlc, test_order, test_payload
else:
    import test_time, test_ohlc, test_order, test_payload

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(test_time))
suite.addTests(loader.loadTestsFromModule(test_ohlc))
suite.addTests(loader.loadTestsFromModule(test_order))
suite.addTests(loader.loadTestsFromModule(test_payload))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
