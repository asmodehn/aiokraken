import glob
import importlib
import os
import unittest

"""
Embedded model tests, to validate knowledge representation on user installation.
uses integrated python tools only.
"""

# even if not in a package, we need to get into one to be able to access aiokraken modules relatively
if __package__ is None:
    import aiokraken.rest.schemas.tests
    __package__ = "aiokraken.rest.schemas.tests"


# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

modules = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))

for m in modules:
    mname = os.path.basename(m)[:-3]
    module = importlib.import_module('.'+mname, package=__package__)

    # add tests to the test suite
    suite.addTests(loader.loadTestsFromModule(module))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)

if result.wasSuccessful():
    exit(0)
else:
    exit(1)
