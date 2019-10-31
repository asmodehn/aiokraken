import marshmallow
from ..exceptions import AIOKrakenSchemaValidationException

class BaseSchema(marshmallow.Schema):
    """ defining common behavior for all schemas """
    class Meta:
        # Pass EXCLUDE as Meta option to keep marshmallow 2 behavior
        # ref: https://marshmallow.readthedocs.io/en/stable/upgrading.html#upgrading-to-3-0
        #unknown = getattr(marshmallow, "EXCLUDE", None)
        # WE EXPECT VALIDATION ERROR !
        pass

    # def loads(self, *args, **kwargs):
    #     try:
    #         return super().loads(*args, **kwargs)
    #     except marshmallow.exceptions.ValidationError as ve:
    #         raise AIOKrakenSchemaValidationException(ve)

    # TODO : attempt to wrap marshmallow exceptions in aiokraken exceptions...

    def load(self, *args, **kwargs):
        try:
            return super(BaseSchema, self).load(*args, **kwargs)
        except marshmallow.exceptions.ValidationError as ve:
            raise AIOKrakenSchemaValidationException(ve)
        except Exception as e:
            raise

    def dump(self, *args, **kwargs):
        try:
            return super(BaseSchema, self).dump(*args, **kwargs)
        except Exception:
            raise

    # def dumps(selfself, *args, **kwargs):
    #     try:
    #         return super().dumps(*args, **kwargs)
    #     except Exception:
    #         raise


class BaseOptionalSchema(marshmallow.Schema):
    class Meta:
        # Pass EXCLUDE as Meta option to keep ignore unknown fields (instead of errorring)
        # ref: https://marshmallow.readthedocs.io/en/stable/upgrading.html#upgrading-to-3-0
        unknown = getattr(marshmallow, "EXCLUDE", None)

    # def loads(self, *args, **kwargs):
    #     try:
    #         return super().loads(*args, **kwargs)
    #     except marshmallow.exceptions.ValidationError as ve:
    #         raise AIOKrakenSchemaValidationException(ve)

    def load(self, *args, **kwargs):
        try:
            return super().load(*args, **kwargs)
        except marshmallow.exceptions.ValidationError as ve:
            raise AIOKrakenSchemaValidationException(ve)

    def dump(self, *args, **kwargs):
        try:
            return super().dump(*args, **kwargs)
        except Exception:
            raise

    # def dumps(selfself, *args, **kwargs):
    #     try:
    #         return super().dumps(*args, **kwargs)
    #     except Exception:
    #         raise
