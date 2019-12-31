"""Signals and slots implementation with asyncio

Slots have to be coroutines. Weak references are used by default.
It will be scheduled to run asynchronously with ``asyncio.create_task()``
(but you must run event loop by yourself).

A modified version of https://raw.githubusercontent.com/xmikos/signaller/master/signaller.py
"""

import asyncio, concurrent.futures, weakref, inspect, logging
from functools import wraps

logger = logging.getLogger(__name__)


def autoconnect(cls):
    """Class decorator for automatically connecting instance methods to signals"""
    old_init = cls.__init__

    @wraps(old_init)
    def new_init(self, *args, **kwargs):
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, '_signals'):
                for sig, sig_kwargs in method._signals.items():
                    sig.connect(method, **sig_kwargs)
        old_init(self, *args, **kwargs)

    cls.__init__ = new_init
    return cls


class Reference:
    """Weak or strong reference to function or method"""
    def __init__(self, obj, callback=None, weak=True, force_async=False):
        if not callable(obj):
            raise TypeError('obj has to be callable')

        self.force_async = force_async
        self._weak = weak
        self._alive = True
        self._hash = obj.__hash__()
        self._repr = obj.__repr__()

        if self.weak:
            if inspect.ismethod(obj):
                self._ref = weakref.WeakMethod(obj, self._wrap_callback(callback))
            else:
                self._ref = weakref.ref(obj, self._wrap_callback(callback))
        else:
            self._ref = obj

    def _wrap_callback(self, callback):
        """Wrap callback to be called with reference to ourselves, not underlying weakref object"""
        def wrapper(obj):
            logger.debug('Object {} has been deleted'.format(self._repr))
            self._alive = False
            if callback is not None:
                return callback(self)
        return wrapper

    @property
    def weak(self):
        """Returns True if this is weak reference"""
        return self._weak

    @property
    def alive(self):
        """Returns True if underlying weak reference is still alive"""
        return self._alive

    def getobject(self):
        """Returns underlying object"""
        return self._ref() if self.weak else self._ref

    def __call__(self, *args, **kwargs):
        return self.getobject()(*args, **kwargs)

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __repr__(self):
        return '<Reference ({}) to {}{}>'.format(
            'weak' if self.weak else 'strong',
            self._repr,
            ' (dead)' if not self.alive else ''
        )


class Signal:
    """Signal emitter"""
    def __init__(self, name='', loop=None):
        self.name = name
        self.loop = loop or asyncio.get_event_loop()
        self._slots = set()

    async def __call__(self, *args, **kwargs):
        """Emit signal (call all connected slots) and block the control flow.
        Note : we do not want to produce a return here (or calling the coroutine directly would do the job).
        So a data structure has to be filled up by hte user to manage that.
        """
        logger.info('Emitting signal {}'.format(self))
        for ref in self._slots:
            logger.debug('Calling coroutine now {}'.format(ref))
            await ref(*args, **kwargs)  # Note : even if we wait, we do not expect return here (or use usual async call)
            # TODO : maybe call for disconnect ? or pass the signal itself to let the method code do it ?

    def emit(self, *args, **kwargs):
        """Emit signal (call all connected slots)
        Note : we do not want to produce a return here (or calling the coroutine directly would do the job).
        So a data structure has to be filled up by hte user to manage that.
        """
        logger.info('Emitting signal {}'.format(self))
        for ref in self._slots:
            assert asyncio.iscoroutinefunction(ref.getobject())
            logger.debug('Scheduling coroutine {}'.format(ref))
            self.loop.create_task(ref(*args, **kwargs))
            # TODO : maybe call for disconnect ? or pass the signal itself to let the method code do it ?

    def clear(self):
        """Disconnect all slots"""
        logger.info('Disconnecting all slots from signal {}'.format(self))
        self._slots.clear()

    def connect(self, *args, weak=True, force_async=False):
        """Connect signal to slot (can be also used as decorator)"""
        def wrapper(func):
            args = inspect.getfullargspec(func).args
            if inspect.isfunction(func) and args and args[0] == 'self':
                logger.debug('Marking instance method {} for autoconnect to signal {}'.format(
                    func, self
                ))
                if not hasattr(func, '_signals'):
                    func._signals = {}
                func._signals[self] = {'weak': weak, 'force_async': force_async}
            else:
                logger.info('Connecting signal {} to slot {}'.format(self, func))
                self._slots.add(
                    Reference(func, callback=self.disconnect, weak=weak, force_async=force_async)
                )
            return func

        # If there is one (and only one) positional argument and this argument is callable,
        # assume it is the decorator (without any optional keyword arguments)
        if len(args) == 1 and callable(args[0]):
            return wrapper(args[0])
        else:
            return wrapper

    def disconnect(self, slot):
        """Disconnect slot from signal"""
        try:
            logger.info('Disconnecting slot {} from signal {}'.format(slot, self))
            self._slots.remove(slot)
        except KeyError:
            logger.warning('Slot {} is not connected!'.format(slot))
            pass

    def __repr__(self):
        return '<Signal {} at {}>'.format(
            '\'{}\''.format(self.name) if self.name else '<anonymous>',
            hex(id(self))
        )
