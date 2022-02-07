import configparser

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


def check_permission(needed_level: str = 'regular'):
    def decorator(func):
        def wrap(self, *args, **kwargs):
            print(kwargs)
            user_permission = Loader.user_privileges.get(kwargs['chat_id'], Privileges.test)
            print(f'usr rer = {user_permission}, needed = {pr_dict[needed_level]}')
            resp = {}
            if user_permission < pr_dict[needed_level]:
                print('DENIED!!!')
                resp['res'] = 'ERROR'
                resp['descr'] = 'Permission denied'
            else:
                print('ALLOWED!!!')
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
