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
    8: 'MARKUP_ERROR',
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

    def send_error(self, trace) -> None:
        if self.context.get('send', False) is True:
            send_dev_message(
                data=dict(
                    subject=self.context['error_type'],
                    text=f"Message: {self.context.get('message')}\nTraceback: {trace}"
                )
            )

    def return_message(self):
        return dict(text=self.context.get('return_message', 'Something wrong'))
