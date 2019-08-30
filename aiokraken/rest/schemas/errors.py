from marshmallow import fields

from ..exceptions import AIOKrakenServerError


# TODO : fillup and refine this
class ErrorsField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ""
        return value

    def _deserialize(self, value, attr, data, **kwargs):
        for e in value:
            raise AIOKrakenServerError(e)  # TODO : find a way to aggregate exceptions...
        return value