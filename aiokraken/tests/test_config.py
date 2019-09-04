import unittest
import parameterized

if not __package__:
    from aiokraken.config import load_api_keyfile
else:
    from..config import load_api_keyfile


class TestLoadKeyFile(unittest.TestCase):

    def test_load_api_keyfile(self):
        r = load_api_keyfile()
        assert 'key' in r
        assert 'secret' in r
        assert len(r.get('key')) == 56
        assert len(r.get('secret')) == 88


