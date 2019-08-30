class AIOKrakenException(Exception):
    pass



class AIOKrakenServerError(AIOKrakenException):
    pass

class AIOKrakenSchemaValidationException(AIOKrakenException):
    pass