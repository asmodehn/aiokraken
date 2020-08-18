
from dataclasses import dataclass

import typing

from marshmallow import fields, post_load, post_dump, pre_load

from aiokraken.rest.schemas.base import BaseSchema


@dataclass(frozen=True)
class SystemStatus:
    connection_id: int
    status: str
    version: str


class SystemStatusSchema(BaseSchema):
    """
    >>> s= SystemStatusSchema()
    >>> s.load({
    ... 'connectionID': 12997236506998204415,
    ... 'event': 'systemStatus',
    ... 'status': 'online',
    ... 'version': '1.0.0'
    ... })
    KAsset(altname='ALTNAME', aclass='ACLASS', decimals=42, display_decimals=7)
    """
    connection_id = fields.Integer(data_key="connectionID")
    event = fields.Constant("systemStatus")
    status = fields.String()
    version = fields.String()

    @post_load
    def build_model(self, data, **kwargs):
        data.pop('event')  # we dont need this any longer
        a = SystemStatus(**data)
        return a

