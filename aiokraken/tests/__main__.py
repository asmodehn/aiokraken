import unittest

"""
Embedded model tests, to validate knowledge representation on user installation.
uses integrated python tools only.
"""


# import your test modules
if __package__ is None:
    __package__ = "aiokraken.tests"
from . import test_config, test_assets

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(test_config))
suite.addTest(loader.loadTestsFromModule(test_assets))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)

if result.wasSuccessful():
    exit(0)
else:
    exit(1)
