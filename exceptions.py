from send_service import send_dev_message


RESPONSE_CODES_MAPPING = {
    0: 'SUCCESS',
    1: 'INTERNET_ERROR',
    2: 'FILE_ERROR',
    3: 'DB_ERROR',
    4: 'CONFIG_ERROR',
    5: 'HTTP_ERROR',
    6: 'PARAMETERS_ERROR',
    7: 'CACHE_ERROR',
    100: 'UNKNOWN_ERROR'
}


class TBotException(Exception):
    """
    Custom exceptions
    Main params:
    code - RESPONSE_CODES_MAPPING
    message - error message for developer
    return_message - message for user
    """

    CODES = RESPONSE_CODES_MAPPING

    def __init__(self, *args, **kwargs):
        self.context = {
            'error_type': self.CODES[kwargs.get('code', 100)],
        }
        for key, value in kwargs.items():
            self.context[key] = value
        super().__init__(*args)

    def send_error(self, trace):
        if self.context.get('send', False) is True:
            send_dev_message(
                data=dict(
                    subject=self.context['error_type'],
                    text=f"Message: {self.context['message']}\nTraceback: {trace}"
                )
            )

    def return_message(self):
        return dict(text=self.context.get('return_message', 'Something wrong'))


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
