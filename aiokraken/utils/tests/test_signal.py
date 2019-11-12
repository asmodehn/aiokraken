import unittest
import aiounittest
# see : https://bugs.python.org/issue32972


if not __package__:
    __package__ = "aiokraken.utils.tests"
from ..signal import Signal


class SignalTestCase(aiounittest.AsyncTestCase):

    async def test_signal_not_connected(self):
        sig = Signal('test_signal')

    async def test_signal_not_connected_emitted(self):
        sig = Signal('test_signal')
        sig.emit()

    async def test_signal_connected_not_emitted(self):
        sig = Signal('test_signal')
        called = False

        async def inner():
            nonlocal called
            called = True

        sig.connect(inner)
        assert called is False

    async def test_signal_connected_emitted(self):
        sig = Signal('test_signal')
        called = False

        async def inner():
            nonlocal called
            called = True

        sig.connect(inner)
        assert called is False
        await sig()
        assert called is True

    async def test_signal_connected_disconnected_emitted(self):
        sig = Signal('test_signal')
        called = False

        async def inner():
            nonlocal called
            called = True

        sig.connect(inner)

        sig.disconnect(inner)
        assert called is False
        await sig()
        assert called is False

    # TODO : maybe we dont need this "instance method" feature ? would simplify things...
    async def test_signal_connected_emitted_alive(self):
        sig = Signal('test_signal')
        called = False

        class Thing:
            async def inner(self):
                nonlocal called
                called = True

        t = Thing()

        sig.connect(t.inner)
        assert called is False
        await sig()
        assert called is True

    async def test_signal_connected_emitted_dead(self):
        sig = Signal('test_signal')
        called = False

        class Thing:
            async def inner(self):
                nonlocal called
                called = True

        t = Thing()
        sig.connect(t.inner)

        assert called is False

        del t
        await sig()  # t.inner automatically disconnected on t delete.

        assert called is False




if __name__ == "__main__":
    unittest.main()
