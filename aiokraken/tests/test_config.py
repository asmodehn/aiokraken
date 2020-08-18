import unittest
import parameterized

if not __package__:
    from aiokraken.config import load_api_keyfile
else:
    from..config import load_api_keyfile


# This is a kind of integration test for the user environment...
# Need to test user environment (and not CI)
class TestLoadKeyFile(unittest.TestCase):

    @unittest.skipIf(load_api_keyfile() is None,
                     "keyfile not detected")
    def test_load_api_keyfile(self):
        r = load_api_keyfile()
        assert 'key' in r
        assert 'secret' in r
        assert len(r.get('key')) == 56
        assert len(r.get('secret')) == 88


