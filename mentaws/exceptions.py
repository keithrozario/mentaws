class SementaraError(Exception):

    """
    Base class for exceptions in this module.
    """

    pass


class InvalidPasswordError(SementaraError):

    """
    Raised when Argument is not supported by the function.
    """

    def __init__(self, message):
        self.message = message
        self.Code = "InvalidPasswordError"
