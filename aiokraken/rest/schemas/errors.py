from marshmallow import fields


# TODO : fillup and refine this
class ErrorsField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ""
        return value

    def _deserialize(self, value, attr, data, **kwargs):
        return value