
import logging
rest_log = logging.getLogger("aiokraken_rest")
rest_log.setLevel(logging.DEBUG)

# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# add the handler to the root logger
rest_log.addHandler(console)

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
        rest_log.info(f"Expecting {schema} ...")
        self.schema = schema

    def __call__(self, status, data, request_data):   # request data as dict (for now) # Goal : display on error)
        assert status == self.status
        # TODO : manage errors here
        rest_log.info(data)
        return self.schema.load(data)
