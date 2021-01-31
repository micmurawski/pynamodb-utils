class FilterError(Exception):
    message = ""
    status_code = 500

    def __init__(self, message=None, status_code=None):
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message, self.status_code)
