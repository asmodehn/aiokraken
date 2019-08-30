import marshmallow


class BaseSchema(marshmallow.Schema):
    """ defining common behavior for all schemas """
    class Meta:
        # Pass EXCLUDE as Meta option to keep marshmallow 2 behavior
        # ref: https://marshmallow.readthedocs.io/en/stable/upgrading.html#upgrading-to-3-0
        #unknown = getattr(marshmallow, "EXCLUDE", None)
        # WE EXPECT VALIDATION ERROR !
        pass