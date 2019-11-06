
import time
import asyncio


# TODO : print -> logging
def synclimiter(period, skippable=False, timer=time.time):
    """
    A synchronous limiter. useful mostly for testing, and sharing code with the useful async limiter.
    :param period:
    :param skippable:
    :param timer:
    :return:
    """
    async def limiter_decorator(async_fun):
        cached_result = None
        last_call = timer()  # calling timer to assume last call on limiter() call.
        # we cannot limit restart of software !
        # So it is better to start slowly, just in case...

        async def wrapper(*args, **kwargs):
            nonlocal cached_result, last_call
            now = timer()
            # CAREFUL with timer,

            epsilon = 1  # needed to workaround inaccurate time measurements on sleep (depend on OS...)

            if cached_result is None or (not skippable and now - last_call < period):
                await asyncio.sleep(period - now + last_call + epsilon)
                now = timer()
            if cached_result is None or now - last_call > period:
                last_call = now
                cached_result = await async_fun(*args, **kwargs)

            return cached_result
        return wrapper
    return limiter_decorator


from collections import namedtuple


PeriodCheck = namedtuple("PeriodCheck", ["last", "now", "period"])


def period_passed(p: PeriodCheck):
    return p.now - p.last > p.period


def limiter(period, timer=time.time, sleeper=asyncio.sleep):
    """
    A limiter for function call to not go under a certain period.
    Note this is quite sensitive code. Performance is not an issue, we might sleep most of the time anyway.
    But safety is paramount : we want extensive maintainability and testability here.
    :param period:
    :param timer:
    :param sleeper:
    :return:
    """

    # To prevent multiple calls at the same time (coroutines are reentrant)
    #  we need a semaphore here, to have unicity of call for a limiter
    sem = asyncio.Semaphore()

    # TODO : for sync usecase, we probably need a thread safe model...

    def maybe_sleepabit_sync(p: PeriodCheck):

        epsilon = 1  # needed to workaround inaccurate time measurements on sleep (depend on OS...)

        if not period_passed(p):
            print(f"Need to sleep {p.period - p.now + p.last + epsilon} secs...")
            sleeper(p.period - p.now + p.last + epsilon)
        return timer()

    async def maybe_sleepabit(p: PeriodCheck):

        epsilon = 1  # needed to workaround inaccurate time measurements on sleep (depend on OS...)

        if not period_passed(p):
            print(f"Need to sleep {p.period - p.now + p.last + epsilon} secs...")
            await sleeper(p.period - p.now + p.last + epsilon)
        return timer()

    def just_callit_sync(fun, args=None, kwargs=None):

        print(f"Call now !")
        args = () if args is None else args
        kwargs = {} if kwargs is None else kwargs
        assert callable(fun), print(f"{fun} not callable!")
        return fun(*args, **kwargs)

    async def just_callit(async_fun, args, kwargs):
        async with sem:  # we need to prevent reentrant calls here, to get linearizability.
            # blocks should be minimal since most of it should be handled by sleeping...
            # TODO : maybe better code structure ?? Some timer + event ? Condition ?
            print(f"Call now !")
            args = () if args is None else args
            kwargs = {} if kwargs is None else kwargs
            assert callable(async_fun), print(f"{async_fun} not callable!")
            return await async_fun(*args, **kwargs)

    def maybe_callit_sync(p: PeriodCheck, fun, *args, **kwargs):
        if period_passed(p):
                return p.now, just_callit_sync(fun, *args, **kwargs)
        else:
            return p.last, None

    async def maybe_callit(p: PeriodCheck, async_fun, *args, **kwargs):
        if period_passed(p):
            return p.now, await just_callit(async_fun, *args, **kwargs)
        else:
            return p.last, None

    # This has to be limiter global, along with period, to allow multi limiter on the same period...
    last_call = timer()  # calling timer to assume last call on limiter() call.
    # we cannot limit restart of software !
    # So it is better to start slowly, just in case...

    def limiter_decorator_params(skippable=False,):

        def limiter_decorator(fun):
            cached_result = None

            def wrapper_sync(*args, **kwargs):
                nonlocal cached_result, last_call

                now = timer()
                if not skippable or cached_result is None:  # if we cannot skip this call, we have to wait.
                    print(f"Call cannot be skipped.")
                    now = maybe_sleepabit_sync(PeriodCheck(last=last_call, now=now, period=period))

                    # Then force call (we don't want to check another time in case it fails because of timer imprecision).
                    # This is a best effort strategy.
                    last_call = now  # now has the new timer, after sleeping a bit
                    cached_result = just_callit_sync(fun=fun, args=args, kwargs=kwargs)

                else:  # if skippable and cached_result
                    print(f"Call can be skipped...")
                    last_call, result = maybe_callit_sync(PeriodCheck(last=last_call, now=now, period=period), fun=fun, args=args, kwargs=kwargs)
                    if result is not None:
                        cached_result = result

                return cached_result

            async def wrapper(*args, **kwargs):
                nonlocal cached_result, last_call

                now = timer()
                if not skippable or cached_result is None:  # if we cannot skip this call, we have to wait.
                    now = await maybe_sleepabit(PeriodCheck(last=last_call, now=now, period=period))

                    # Then force call (we don't want to check another time in case it fails because of timer imprecision).
                    # This is a best effort strategy.
                    last_call = now  # now has the new timer, after sleeping a bit
                    cached_result = await just_callit(async_fun=fun, args=args, kwargs=kwargs)

                else:  # if skippable and cached_result
                    last_call, result = await maybe_callit(PeriodCheck(last=last_call, now=now, period=period), async_fun=fun,
                                                          args=args, kwargs=kwargs)
                    if result is not None:
                        cached_result = result

                return cached_result

            if asyncio.iscoroutinefunction(func=fun):
                return wrapper
            else:
                return wrapper_sync

        return limiter_decorator
    return limiter_decorator_params

if __name__ == "__main__":
    import pytest

    pytest.main(["-s", "--doctest-modules", "--doctest-continue-on-failure", __file__])
