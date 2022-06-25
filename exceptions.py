class TBotException(Exception):
    ...


class FileDBNotFoundError(TBotException):
    def __init__(self, file_name):
        self.file_name = file_name
        super().__init__(file_name)


class ConfigAttributeNotFoundError(TBotException):
    def __init__(self, attr_name):
        self.attr_name = attr_name
        super().__init__(attr_name)


class EmptySoupDataError(TBotException):
    def __init__(self, url=''):
        self.url = url
        super().__init__(url)


class BadResponseStatusError(TBotException):
    def __init__(self, status_code):
        self.status_code = status_code
        super().__init__(status_code)


class WrongParameterTypeError(TBotException):
    def __init__(self, param):
        self.param = param
        super().__init__(param)


class UnknownError(TBotException):
    def __init__(self):
        super().__init__(f'Unknown error')
