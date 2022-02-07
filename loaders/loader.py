import configparser
import logging

pr_dict = {
    'untrusted': 10,
    'test': 20,
    'regular': 30,
    'trusted': 40,
    'root': 50
}


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
        def wrap(self, *args, **kwargs):
            logger.info(f'check permission')
            user_permission = Loader.user_privileges.get(kwargs['chat_id'], Privileges.test)
            logger.info(f'User permission: {user_permission}, needed permission = {pr_dict[needed_level]}')
            resp = {}
            if user_permission < pr_dict[needed_level]:
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
