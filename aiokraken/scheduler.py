
"""Note this is a decorator like limiter.
Except that the focus here is to attempt to not go too far under a certain period of call.
It is somewhat teh complement of the limiter
"""

import time
import asyncio

# TODO : print -> logging
from collections import namedtuple

from aiokraken.rest.exceptions import AIOKrakenServerError

PeriodCheck = namedtuple("PeriodCheck", ["last", "now", "period"])


def scheduler(period, timer=time.time, sleeper=asyncio.sleep):
    """
    A scheduler for function call to not go above a certain period.
    Note this is quite sensitive code. Performance is not an issue, we might sleep most of the time anyway.
    But safety is paramount : we want extensive maintainability and testability here.
    :param period:
    :param timer:
    :param sleeper:
    :return:
    """

    # Ref : https://en.wikipedia.org/wiki/Control_theory

    def inside_period(p: PeriodCheck):
        return p.now - p.last < p.period

    async def maybe_sleepabit(p: PeriodCheck):
        epsilon = 1  # needed to workaround inaccurate time measurements on sleep (depend on OS...)
        # TODO :maybe link this somehow with limiter's epsilon

        if inside_period(p):
            print(f"Need to sleep {p.period - p.now + p.last - epsilon} secs...")
            await sleeper(p.period - p.now + p.last - epsilon)
        return timer()

    async def just_callit(async_fun, args, kwargs):

        # TODO : maybe better code structure ?? Some timer + event ? Condition ?
        print(f"Call now !")
        args = () if args is None else args
        kwargs = {} if kwargs is None else kwargs
        assert callable(async_fun), print(f"{async_fun} not callable!")
        result= await async_fun(*args, **kwargs)
        return result

    async def maybe_callit(p: PeriodCheck, async_fun, *args, **kwargs):
        if not inside_period(p):
            return p.now, await just_callit(async_fun, *args, **kwargs)
        else:
            return p.last, None

    # This has to be scheduler global, along with period, to allow multi scheduler on the same period...
    last_call = 0  # taking minimum value to assume never called.

    # we cannot force restart of software !
    # So it is better to start aggressively, just in case...

    def scheduler_decorator_params():  # if we want to add instance level parameters later (just like for limiter)

        def scheduler_decorator(fun):

            async def wrapper(*args, **kwargs):
                nonlocal last_call

                # Maybe sleep on entrance (to not block controlflow on return...)
                now = await maybe_sleepabit(PeriodCheck(last=last_call, now=timer(), period=period))

                # We attempt to use the controlflow we have while we have it...
                last_call, result = await maybe_callit(PeriodCheck(last=last_call, now=now, period=period), async_fun=fun,
                                                       args=args, kwargs=kwargs)

                if result is None:

                    # Then call (we have control flow now, meaning the call is intended, so we should use it asap).
                    # This is a best effort strategy.
                    last_call = now  # now has the new timer, after sleeping a bit
                    result = await just_callit(async_fun=fun, args=args, kwargs=kwargs)

                # trampoline for tail recursive loop
                asyncio.create_task(wrapper(*args, **kwargs))

                return result

            if asyncio.iscoroutinefunction(func=fun):
                return wrapper
            else:
                raise NotImplementedError

        return scheduler_decorator

    return scheduler_decorator_params


if __name__ == "__main__":
    import pytest

    pytest.main(["-s", "--doctest-modules", "--doctest-continue-on-failure", __file__])
