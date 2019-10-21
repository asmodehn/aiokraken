
from .utils import get_kraken_logger


logger = get_kraken_logger('LoggerBot')


class LoggerBot:
    """
    A very basic default bot, periodically logging various stuff...
    """

    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        print(logger.info(f"{args}, {kwargs}"))
