import logging
from functools import wraps

import config

logger = logging.getLogger(__name__)
handler = logging.FileHandler('run.log')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


def check_permission(needed_level: str = 'regular'):
    """
    Decorator, which check user permission
    Each function with this decorator need consist "**kwargs" in its attributions and receive the parameter
    "check_id" when called
    @check permission(needed_level='level') ('untrusted', 'test', 'regular', 'trusted', 'root')
    function(self, **kwargs)
    :param needed_level: permission level needed to get func result
    :return: wrapped function
    """
    def decorator(func):
        @wraps(func)
        def wrap(self, *args, **kwargs):
            logger.info(func.__qualname__)
            logger.info(f'check permission')
            if needed_level not in Loader.privileges_levels.keys():
                logger.error(f'{needed_level} is not permission level name')
            user_permission = kwargs['privileges']
            logger.info(f'User permission: {user_permission}, '
                        f'needed permission: {Loader.privileges_levels[needed_level]}')
            if user_permission < Loader.privileges_levels[needed_level]:
                logger.info('Access denied')
                return Loader.error_resp('Permission denied')
            else:
                logger.info('Access allowed')
                resp = func(self, *args, **kwargs)
            return resp
        return wrap
    return decorator


class Loader:
    """
    Common loaders class
    """

    loaders = []
    users = {}

    privileges_levels = {
        'untrusted': 10,
        'test': 20,
        'regular': 30,
        'trusted': 40,
        'root': 50
    }

    def __init__(self, name):
        self.name = name
        Loader.loaders.append(self.name)

    @staticmethod
    def get_loaders():
        """
        Get all available loaders
        """
        return Loader.loaders

    @staticmethod
    def error_resp(error_text: str = 'Something wrong'):
        """
        Return error response with variable text
        :param error_text: error description string
        :return: error response
        """
        resp = dict()
        resp['text'] = error_text
        return resp

    @staticmethod
    def dict_to_str(di: dict, delimiter: str = ' = ') -> str:
        """
        Turn dict to str
        Digit not use
        Keys "res" and "chat_id" is skipping
        Example:
             {1: 'text'} => 'text'
             {'key': 'value'}, '=' => 'key = value'
             {'key1': 'value1', 'key2': 'value2'}, ': ' => key1: value1\nkey2: value2
        :param di: input dict
        :param delimiter: delimiter string
        :return: string
        """
        fin_str = ''
        for key, value in di.items():
            if isinstance(key, int):
                fin_str += f'{value}\n'
            else:
                fin_str += f'{key}{delimiter}{value}\n'
        return fin_str

    @staticmethod
    def get_root_users() -> list:
        root_users = []
        for key, value in Loader.users.items():
            if value['value'] == Loader.privileges_levels['root']:
                root_users.append(key)
        return root_users

    @staticmethod
    def is_phone_number(number: str) -> str or None:
        """
        Check string. If non phone number, return None. Else return formatted phone number
        :param number: any format of phone number
        :return: formatted phone number
        """
        resp = {}
        if len(number) < 10 or len(number) > 18:
            return None
        allowed_simbols = '0123456789+()- '
        for num in number:
            if num not in allowed_simbols:
                return None
        raw_num = number
        raw_num = raw_num.strip()
        raw_num = raw_num.replace(' ', '')
        raw_num = raw_num.replace('+', '')
        raw_num = raw_num.replace('(', '')
        raw_num = raw_num.replace(')', '')
        raw_num = raw_num.replace('-', '')
        if len(raw_num) < 11:
            raw_num = '8' + raw_num
        if raw_num.startswith('7'):
            raw_num = '8' + raw_num[1:]
        if not raw_num.startswith('89'):
            resp['res'] = 'ERROR'
            resp['descr'] = 'Number format is not valid'
            return None
        return raw_num
