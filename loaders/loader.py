from functools import wraps
from sqlalchemy import exc

import config
from loggers import get_logger
from models import LibPrivileges

logger = get_logger(__name__)


def check_permission(needed_level: str = 'regular'):
    """
    Decorator, which check user permission
    Each function with this decorator need consist "**kwargs" in its attributions and receive the parameter
    "privileges" when called
    @check permission(needed_level='level') ('untrusted', 'test', 'regular', 'trusted', 'root')
    function(self, **kwargs)
    :param needed_level: permission level needed to get func result
    :return: wrapped function
    """
    def decorator(func):
        @wraps(func)
        def wrap(self, *args, **kwargs):
            logger.info(f'Check permission')
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
                logger.info(func.__qualname__)
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
    if config.USE_DB:
        try:
            privileges_levels = {privileges.name: privileges.value
                                 for privileges in LibPrivileges.query.with_entities(LibPrivileges.name,
                                                                                     LibPrivileges.value).all()}
        except exc.DatabaseError as e:
            logger.exception(f'DB connection error: {e}')
            privileges_levels = config.PRIVILEGES_LEVELS
    else:
        privileges_levels = config.PRIVILEGES_LEVELS

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
    def get_root_users() -> list:
        root_users = []
        for key, value in Loader.users.items():
            if value['value'] == Loader.privileges_levels['root']:
                root_users.append(key)
        return root_users
