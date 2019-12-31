import hashlib
import hmac
import urllib
import base64
from dataclasses import dataclass, asdict, field
from ..utils import get_nonce
from .response import Response
import typing

import logging
rest_log = logging.getLogger("aiokraken_rest")
rest_log.setLevel(logging.DEBUG)


"""
A dataclass representing a request
"""
def _sign_message(data, url_path, secret):
    """
        Kraken message signature for private user endpoints
        https://www.kraken.com/features/api#general-usage
        url_path starts from the root (like "/<version>/private/endpoint")
    """
    post_data = urllib.parse.urlencode(data)

    # Unicode-objects must be encoded before hashing
    encoded = (str(data['nonce']) + post_data).encode()
    message = url_path.encode() + hashlib.sha256(encoded).digest()
    signature = hmac.new(
        base64.b64decode(secret),
        message,
        hashlib.sha512
    )
    sig_digest = base64.b64encode(signature.digest())

    return sig_digest.decode()


@dataclass(frozen=False)
class Request:
    """
    Request : Mutable or immutable ? (with state monad style management ?)
    Idempotent call (or 'retry' semantic ? based on error code ?)
    """

    urlpath: str = ""
    data: typing.Dict = field(default_factory=dict)
    headers: typing.Dict = field(default_factory=dict)
    expected: typing.Optional[Response] = None

    def __post_init__(self):
        rest_log.info(f"{self.urlpath}: {self.data}")
        rest_log.debug(f"{self.headers}")

    async def __call__(self, response):
        """
        Locally modelling the request.
        returning possible responses, and how to deal with them
        :return:
        """
        res = await response.json(encoding='utf-8', content_type=None)
        rest_log.debug(f"{res}")
        parsed_res = self.expected(status=response.status, data=res, request_data=asdict(self))  # validating response data
        return parsed_res

    def sign(self, key, secret):

        self.data['nonce'] = get_nonce()
        # If key OR secret are none, we do not sign...
        # Maybe dangerous ? But we need something similar to be able to test private URL without signing (when we work with cassettes)
        if key is not None:
            self.headers['API-Key'] = key
        if secret is not None:
            self.headers['API-Sign'] = _sign_message(self.data, self.urlpath, secret)

        return self


