
class Response():
    """
    Response: structure validating response against expected schema
    """

    def __init__(self, status, schema):
        """
        :param status: status possible for this response
        :param schema: schema to validate against
        """
        self.status = status
        self.schema = schema

    def __call__(self, status, data, request_data):   # request data as dict (for now) # Goal : display on error)
        assert status == self.status
        # TODO : manage errors here
        return self.schema.load(data)
