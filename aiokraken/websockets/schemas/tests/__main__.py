import unittest

"""
Embedded model tests, to validate knowledge representation on user installation.
uses integrated python tools only.
"""


# import your test modules
if __package__ is not None:
    from . import test_heartbeat, test_ping, test_pong
else:
    import  test_heartbeat, test_ping, test_pong

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(test_heartbeat))
suite.addTests(loader.loadTestsFromModule(test_ping))
suite.addTests(loader.loadTestsFromModule(test_pong))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)

if result.wasSuccessful():
    exit(0)
else:
    exit(1)
