import unittest

# TODO: move this into doctest
# TODO : property based testing (hypothesis)

def proctest_noreturn(arg1: int, arg2:str):
    return 42

def proctest_return(arg1: int, arg2: str) -> int:
    return 42

def gentest_noreturn(arg1: int):
    yield 42
    yield 47
    yield 51

def gentest_return(arg1: int) -> int:
    yield 42
    yield 47
    yield 51

async def corotest_noreturn(arg1: int):
    return 42

async def corotest_return(arg1: int) -> int:
    return 42


class TestFramableDef(unittest.TestCase):

    def methodtest_noreturn(self, arg: int):
        return 42

    def methodtest_return(self, arg: int) -> int:
        return 42

    def test_procedure(self):
        raise NotImplementedError


    def test_generator(self):
        raise NotImplementedError


    def test_coroutine(self):
        raise NotImplementedError


    def test_methode(self):
        raise NotImplementedError


    def test_class(self):
        raise NotImplementedError


if __name__ == '__main__':
    unittest.main()




