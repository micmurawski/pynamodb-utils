class Error(Exception):
    def __init__(self, message: dict) -> None:
        self.message = message
        super().__init__(message)


class FilterError(Error):
    pass


class SerializerError(Error):
    pass
