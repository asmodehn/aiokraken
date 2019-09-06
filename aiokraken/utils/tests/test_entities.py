import asyncio
import functools
import os
import signal
import time

from ..entities import Entity, reset, on_signal

import unittest




# class TestEntity(unittest.TestCase):
#     pass


# class TestReset(unittest.TestCase):
#     raise NotImplementedError
    # TODO : how to ? tasks are not accessible if eventloop not running... in asyncio
    # def test_reset_task_created(self):
    #
    #     @reset()
    #     async def mycoro():  # TODO : mock ?
    #         await asyncio.sleep(0.1)
    #
    #     # verifying that just declaring a reset coro stores it in the list.
    #     assert mycoro in asyncio.all_tasks()


class TestOnSignal(unittest.TestCase):
    def test_on_signal_handler(self):

        value = 42

        # TODO : mock ?
        @on_signal(signal.SIGUSR1)
        async def ask_exit(sig_name):
            nonlocal value
            value=51

        # returns true if a signal handler was removed (as per the doc)
        assert asyncio.get_event_loop().remove_signal_handler(signal.SIGUSR1)

        # TODO : an integration test to test outside the package (wth POpen and hte like...)
        # assert value == 42
        # # careful with this and test framework that do not create extra processes for tests...
        # os.kill(os.getpid(), signal.SIGUSR1)
        # # OR pthread_kill ??
        #
        # # TODO : some async timeout cleanup ?
        # timeout = time.time() + 2  # 2 seconds sync timeout
        # while time.time() < timeout and value != 51:
        #     # usual blocking sleep waiting for signal
        #     time.sleep(0.1)
        # assert value == 51  # otherwise timeout happened
