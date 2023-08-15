from functools import wraps
from sqlalchemy import exc
from telebot.types import InlineKeyboardMarkup

import config
from extentions import db
from loggers import get_logger
from models import LibPrivileges, LogRequests

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
        def wrap(self, request: LoaderRequest) -> LoaderResponse:
            logger.info(f'Check permission')
            if needed_level not in Loader.privileges_levels.keys():
                logger.error(f'{needed_level} is not permission level name')
            user_permission = request.privileges
            logger.info(f'User permission: {user_permission}, '
                        f'needed permission: {Loader.privileges_levels[needed_level]}')
            if user_permission < Loader.privileges_levels[needed_level]:
                logger.info('Access denied')
                return LoaderResponse(text='Permission denied')
            else:
                logger.info('Access allowed')
                logger.info(func.__qualname__)
                resp = func(self, request)
            return resp
        return wrap
    return decorator


class Loader:
    """
    Common loaders class
    """

    if config.USE_DB:
        try:
            privileges_levels = {privileges.name: privileges.value
                                 for privileges in LibPrivileges.query.with_entities(LibPrivileges.name,
                                                                                     LibPrivileges.value).all()}
        except exc.DatabaseError as e:
            logger.exception(f'DB connection error: {e}')
            privileges_levels = config.PRIVILEGES_LEVELS
            exit()
    else:
        privileges_levels = config.PRIVILEGES_LEVELS


class LoaderRequest:
    def __init__(
        self,
        text: str,
        privileges: int,
        chat_id: str
    ):
        self.text = text
        self.privileges = privileges
        self.chat_id = chat_id

class LoaderResponse:
    def __init__(
        self,
        text: str = None,
        photo: str = None,
        chat_id: int or list = None,
        markup: InlineKeyboardMarkup = None,
        parse_mode: str = None,
        is_extra_log: bool = True  # Нужно ли логировать название функции
    ):
        self.text = text
        self.photo = photo
        self.chat_id = chat_id
        self.markup = markup
        self.parse_mode = parse_mode
        self.is_extra_log = is_extra_log

    @staticmethod
    def extra_log(request_id: int, action: str):
        lr = LogRequests.query.filter(
            LogRequests.lr_id == request_id
        ).one_or_none()
        if lr:
            lr.action = action
            db.session.commit()
