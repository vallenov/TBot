import configparser
import logging


class Privileges:
    untrusted = 10
    test = 20
    regular = 30
    trusted = 40
    root = 50


logger = logging.getLogger(__name__)
handler = logging.FileHandler('run.log')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


def check_permission(needed_level: str = 'regular'):
    def decorator(func):
        """
        Decorator, which check user permission
        Each function with this decorator need consist "**kwargs" in its attributions and receive the parameter
        "check_id" when called
        @check permission(needed_level='level') ('untrusted', 'test', 'regular', 'trusted', 'root')
        function(self, **kwargs)
        :param func: input function
        :return: wrapped function
        """
        def wrap(self, *args, **kwargs):
            logger.info(f'check permission')
            if needed_level not in Loader.privileges_levels.keys():
                logger.error(f'{needed_level} is not permission level name')
            user_permission = Loader.user_privileges.get(kwargs['chat_id'], Privileges.test)
            logger.info(f'User permission: {user_permission}, '
                        f'needed permission: {Loader.privileges_levels[needed_level]}')
            resp = {}
            if user_permission < Loader.privileges_levels[needed_level]:
                logger.info('Access denied')
                resp['res'] = 'ERROR'
                resp['descr'] = 'Permission denied'
            else:
                logger.info('Access allowed')
                resp = func(self, *args, **kwargs)
            return resp
        return wrap
    return decorator


class Loader:
    loaders = []
    user_privileges = {}

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
        self._get_config()

    def _get_config(self):
        self.config = configparser.ConfigParser()
        self.config.read('TBot.ini', encoding='windows-1251')

    @staticmethod
    def get_loaders():
        return Loader.loaders

    @staticmethod
    def error_resp(error_text: str):
        resp = {}
        resp['res'] = 'ERROR'
        resp['descr'] = error_text
        return resp
