class TBotException(Exception):
    ...


class FileDBNotFoundError(TBotException):
    """
    When file with poems (for example) is not found
    """
    def __init__(self, file_name):
        self.file_name = file_name
        super().__init__(file_name)


class ConfigAttributeNotFoundError(TBotException):
    """
    When attribute is not found in config
    """
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


class WrongParameterCountError(TBotException):
    """
    When wrong numbers of parameters
    """
    def __init__(self, cnt):
        self.cnt = cnt
        super().__init__(cnt)


class WrongParameterValueError(TBotException):
    """
    When not allowed value found
    """
    def __init__(self, val):
        self.val = val
        super().__init__(val)


class UnknownError(TBotException):
    def __init__(self):
        super().__init__(f'Unknown error')


class NotFoundInDatabaseError(TBotException):
    """
    When nothing is found in DB table
    """
    def __init__(self, tablename):
        self.tablename = tablename
        super().__init__(tablename)


class UserNotFoundError(TBotException):
    """
    When user not found in memory
    """
    def __init__(self, chat_id):
        self.chat_id = chat_id
        super().__init__(chat_id)


class EmptyCacheError(TBotException):
    """
    When data in cache not found
    """
    def __init__(self, param):
        self.param = param
        super().__init__(param)
