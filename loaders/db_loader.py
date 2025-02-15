import random
import datetime
from mysql.connector.errors import OperationalError
import traceback
from sqlalchemy import cast, Date, exc, desc
from sqlalchemy.sql import func

import config

from loaders.loader import Loader, check_permission, LoaderResponse, LoaderRequest
from helpers import (
    dict_to_str,
    cut_commands,
    MarkDown as mdown,
)
import models as md
from extentions import db
from markup import custom_markup
from send_service import send_dev_message
from loggers import get_logger
from exceptions import TBotException
from graph import Graph, BaseGraphInfo, BaseSubGraphInfo
from users import tbot_users

logger = get_logger(__name__)


class DBLoader(Loader):
    """
    Work with DB
    """

    def __init__(self):
        if config.USE_DB:
            self.get_users_from_db()
            logger.info('Connection to DB success')
        else:
            self.get_users_from_config()
            logger.info('Load from config success')

    @staticmethod
    def get_users_from_db() -> None:
        """
        Get all users' information from DB to memory
        """
        logger.info('get_users_from_db')
        try:
            users = md.Users.query \
                .join(
                    md.LibPrivileges,
                    md.Users.privileges_id == md.LibPrivileges.p_id
                ) \
                .add_columns(md.Users.chat_id,
                             md.Users.login,
                             md.Users.first_name,
                             md.LibPrivileges.value,
                             md.Users.description,
                             md.Users.active) \
                .all()
            if not users:
                raise TBotException(code=3, message='TBot.users is empty', send=True)
        except exc.DatabaseError:
            logger.info('Error connection to DB')
            send_dev_message(data={'text': f'Ошибка подключения к БД'}, by='telegram')
            exit()
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            exit()
        tbot_users.add_users(users)

    @staticmethod
    def get_users_from_config() -> None:
        """
        Get all users' information from config to memory
        """
        logger.info('get_users_fom_config')
        try:
            if not config.USERS:
                raise TBotException(code=4, message='USERS')
            tbot_users.add_users(config.USERS.values())
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            exit()

    @staticmethod
    def _get_p_id(privileges: int) -> int or None:
        """
        Get privileges id by privileges value
        """
        try:
            data = md.LibPrivileges.query.filter(
                md.LibPrivileges.value == privileges
            ).one_or_none()
            if not data:
                raise TBotException(code=3, message=f'Privilege {privileges} not found')
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return None
        else:
            return data.p_id

    @staticmethod
    def _get_privileges(p_id: int) -> int or None:
        """
        Get privileges id by privileges value
        """
        try:
            data = md.LibPrivileges.query.filter(
                md.LibPrivileges.p_id == p_id
            ).one_or_none()
            if not data:
                raise TBotException(code=3, message=f'P_id {p_id} not found')
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return None
        else:
            return data.value

    @staticmethod
    def log_request(chat_id: str) -> md.LogRequests:
        """
        Insert base request info to DB
        :param chat_id: person chat_id
        :param action: user action
        :return:
        """
        try:
            req = md.LogRequests(
                chat_id=chat_id
            )
            db.session.add(req)
            db.session.commit()
            return req
        except (OperationalError, exc.OperationalError) as e:
            logger.exception(f'DB connection error: {e}')
            raise

    def add_user(self, chat_id: str, login: str, first_name: str, privileges: int) -> None:
        """
        Add new user to DB and memory
        """
        logger.info('add_user')
        try:
            if config.USE_DB:
                p_id = self._get_p_id(privileges)
                db.session.add(md.Users(chat_id=chat_id,
                                        login=login,
                                        first_name=first_name,
                                        privileges_id=p_id))
                db.session.commit()
        except (OperationalError, exc.OperationalError) as e:
            logger.exception(f'DB connection error: {e}')
            raise
        logger.info(f'New user {chat_id} added')
        tbot_users.add_user(
            chat_id=chat_id,
            login=login,
            first_name=first_name,
            privileges=privileges
        )

    @staticmethod
    def update_user(chat_id: str, login: str, first_name: str) -> None:
        """
        Update user info in DB and memory
        :param chat_id: unique user_id
        :param login: login
        :param first_name: first_name
        """
        logger.info('update_user')
        if config.USE_DB:
            user = md.Users.query.filter(md.Users.chat_id == chat_id).one_or_none()
            user.login = login
            user.first_name = first_name
            db.session.commit()
        tbot_users(chat_id).login = login
        tbot_users(chat_id).first_name = first_name
        logger.info('User info updated')

    @check_permission(needed_level='root')
    def update_user_data(self, request: LoaderRequest) -> LoaderResponse:
        """
        Update user privileges in DB and memory
        """
        resp = LoaderResponse()
        cmd = request.text.split()
        try:
            if len(cmd) < 4:
                raise TBotException(code=6,
                                    return_message=f'Неправильное количество параметров: {len(cmd)}',
                                    parameres_count=len(cmd))
            else:
                chat_id = cmd[2]
                try:
                    if cmd[1].lower() == 'description':
                        new_value = cut_commands(text=request.text, count_of_commands=3)
                    elif cmd[1].lower() == 'privileges':
                        new_value = int(cmd[3])
                    elif cmd[1].lower() == 'active':
                        new_value = bool(int(cmd[3]))
                    else:
                        raise TBotException(
                            code=6,
                            return_message=f'Неправильное значение параметра: {cmd[1]}'
                        )
                except TBotException:
                    raise
                except ValueError:
                    raise TBotException(
                        code=6,
                        return_message=f'Неправильный тип параметра: {cmd[3]}',
                    )
            if config.USE_DB:
                logger.info(f'Updating DB')
                user = md.Users.query.filter(
                    (md.Users.chat_id == chat_id) |
                    (md.Users.login == chat_id) |
                    (md.Users.first_name == chat_id)
                ).all()
                if not user:
                    raise TBotException(code=3, return_message=f'Пользователь {chat_id} не найден')
                if len(user) > 1:
                    raise TBotException(code=3, return_message='Найдено несколько пользователей')
                if cmd[1] == 'privileges':
                    new_value = self._get_p_id(new_value)
                for u in user:
                    chat_id = u.chat_id
                    if cmd[1] == 'description':
                        u.description = new_value
                    elif cmd[1] == 'privileges':
                        u.privileges_id = new_value
                    elif cmd[1] == 'active':
                        u.active = new_value
                db.session.commit()
            logger.info(f'Updating memory')
            if cmd[1] == 'privileges':
                tbot_users(chat_id).privileges = new_value
            elif cmd[1] == 'description':
                tbot_users(chat_id).description = new_value
            elif cmd[1] == 'active':
                tbot_users(chat_id).active = new_value
            logger.info(f'User {chat_id} {cmd[1]} updated')
            resp.text = f'User {chat_id} {cmd[1]} updated'
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def show_users(self, request: LoaderRequest) -> LoaderResponse:
        """
        Show current users information
        """
        resp = LoaderResponse()
        try:
            lst = request.text.split()
            if len(lst) == 1:
                users = [f"{user.chat_id} {user.login} {user.first_name}" for user in tbot_users.all()
                         if user.privileges <= Loader.privileges_levels['trusted']]
                resp.text = 'Список пользователей'
                resp.markup = custom_markup(
                    command='users',
                    category=users,
                    smile='👥'
                )
            elif len(lst) == 2:
                if not tbot_users(lst[1]):
                    raise TBotException(code=3, return_message=f'Пользователь {lst[1]} не найден')
                # user_info = {'chat_id': mdown.fixed_width(lst[1])}
                user = tbot_users(lst[1])
                user.chat_id = mdown.fixed_width(user.chat_id)
                out_text = dict_to_str(user.as_dict(), ': ')
                resp.text = out_text.replace('_', ' ')
                resp.parse_mode = 'MarkdownV2'
            else:
                raise TBotException(code=6, return_message=f'Неверное количество параметров: {len(lst)}')
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def send_other(self, request: LoaderRequest) -> LoaderResponse:
        """
        Send message to other user
        :param request: string "command chat_id message"
        :return: dict {'chat_id': 1234567, 'text': 'some'}
        """
        resp = LoaderResponse()
        lst = request.text.split()
        try:
            if len(lst) < 3:
                raise TBotException(code=6, return_message=f'Неправильное количество параметров: {len(lst)}')
            try:
                chat_id = int(lst[1])
            except ValueError:
                raise TBotException(code=6, return_message=f'Неправильное значение параметра: {lst[1]}')
            if str(chat_id) not in tbot_users:
                raise TBotException(code=3, return_message=f'Пользователь {lst[1]} не найден')
            resp.chat_id = chat_id
            resp.text = cut_commands(text=request.text, count_of_commands=2)
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def send_to_all_users(self, request: LoaderRequest) -> LoaderResponse:
        """
        Send message to all users
        :param request: string "command chat_id message"
        :return: dict {'chat_id': [1234567, 4637499], 'text': 'some'}
        """
        resp = LoaderResponse()
        lst = request.text.split()
        try:
            if len(lst) < 2:
                raise TBotException(code=6, return_message=f'Неправильное количество параметров: {len(lst)}')
            resp.chat_id = []
            for user in tbot_users.active():
                try:
                    chat_id = int(user.chat_id)
                except ValueError:
                    logger.exception(f'Chat {chat_id} is not convert to int')
                resp.chat_id.append(chat_id)
            resp.text = cut_commands(text=request.text, count_of_commands=1)
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission()
    def send_to_admin(self, request: LoaderRequest) -> LoaderResponse:
        """
        Send message to admin
        :param request: request
        :return: dict {'chat_id': admin_id, 'text': 'some'}
        """
        resp = LoaderResponse()
        lst = request.text.split()
        try:
            if len(lst) < 2:
                raise TBotException(code=6, return_message=f'Неправильное количество параметров: {len(lst)}')
            resp.chat_id = int(config.USERS['root_id']['chat_id'])
            resp.text = str(f"Message from {tbot_users(request.chat_id).first_name or request.chat_id}\n"
                            f"Text: {cut_commands(text=request.text, count_of_commands=1)}")
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @staticmethod
    def _get_random_poem():
        """
        Get random poem
        """
        max_id = db.session.query(func.max(md.Poems.p_id)).scalar()
        min_id = db.session.query(func.min(md.Poems.p_id)).scalar()
        random_id = random.randint(min_id, max_id + 1)
        return md.Poems.query.filter(
                md.Poems.p_id == random_id
            ).one_or_none()

    @check_permission()
    def get_poem(self, request: LoaderRequest) -> LoaderResponse:
        """
        Get poem from DB
        :param:
        :return: poesy string
        """
        resp = LoaderResponse()
        count = 10  # максимальное количество вариантов стихов, которые выдаются методом
        try:
            if config.USE_DB:
                lst = request.text.split()
                if len(lst) == 1:
                    poem = self._get_random_poem()
                    if not poem:
                        raise TBotException(code=3, message='Стих не найден')
                    resp.text = f"{poem.author}\n\n{poem.name}\n\n{poem.text}"
                    return resp
                else:
                    try:
                        poem_id = int(lst[1])
                    except ValueError:
                        poem_id = None
                    if len(lst) == 2 and poem_id is not None:
                        poem = md.Poems.query.filter(md.Poems.p_id == poem_id).first()
                        resp.text = f"{poem.author}\n\n{poem.name}\n\n{poem.text}"
                        return resp
                    else:
                        search_string = ' '.join(lst[1:])
                        poems = md.Poems.query.filter(
                            md.Poems.author.like(f'%{search_string}%') |
                            md.Poems.name.like(f'%{search_string}%') |
                            md.Poems.text.like(f'%{search_string}%')
                        ).order_by(
                            md.Poems.author
                        ).all()
                    if not poems:
                        raise TBotException(code=3, return_message='По вашему запросу ничего не найдено')
                    if len(poems) == 1:
                        resp.text = f"{poems[0].author}\n\n{poems[0].name}\n\n{poems[0].text}"
                        return resp
                    else:
                        poems_ids = []
                        poems = poems if len(poems) < count else poems[:count]
                        for poem in poems:
                            poems_ids.append(f'{poem.p_id} {poem.author}. {poem.name}')
                        resp.text = 'Вот, несколько стихов, подходящих под описание'
                        resp.markup = custom_markup(
                            command='poem',
                            category=poems_ids,
                            smile='🪶',
                            cut_id=True
                        )
                        return resp
            else:
                raise TBotException(code=3, return_message='Нет подключения к БД')
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission()
    def poem_divination(self, request: LoaderRequest) -> LoaderResponse:
        """
        Poem divination
        """
        resp = LoaderResponse()
        try:
            cmd = request.text.split()
            if request.chat_id not in tbot_users:
                raise TBotException(code=3, message=f'User {request.chat_id} not found')
            if not tbot_users(request.chat_id).cache:
                tbot_users(request.chat_id).cache = dict()
            if len(cmd) == 1:
                if 'poem' in tbot_users(request.chat_id).cache:
                    tbot_users(request.chat_id).cache.pop('poem')
                if not tbot_users(request.chat_id).cache.get('poem'):
                    while True:
                        poem = self._get_random_poem()
                        count_of_quatrains = poem.text.count('\n\n')
                        if count_of_quatrains == 1:
                            lines = poem.text.split('\n')
                            buf = ''
                            quatrains = []
                            for line in lines:
                                buf += line
                                if buf.count('\n') == 4:
                                    quatrains.append(buf)
                                buf = ''
                            count_of_quatrains = len(quatrains)
                        if count_of_quatrains:
                            break
                    tbot_users(request.chat_id).cache['poem'] = poem
                    resp.text = 'Выберите четверостишие'
                    resp.markup = custom_markup(
                        command='divination',
                        category=[str(i) for i in range(1, count_of_quatrains + 1)],
                        smile='🔮'
                    )
                    resp.is_extra_log = False
                    return resp
            else:
                poem = tbot_users(request.chat_id).cache.get('poem')
                if not poem:
                    raise TBotException(code=7,
                                        return_message=f'Отсутствует сохраненный стих. Нажми на гадание еще разок',
                                        chat_id=request.chat_id,
                                        cache_field='poem')
                quatrains = poem.text.split('\n\n')
                cmd = request.text.split()
                try:
                    number_of_quatrain = int(cmd[1])
                    resp.text = quatrains[number_of_quatrain - 1]
                except ValueError:
                    raise TBotException(code=6, return_message=f'Неправильный тип параметра {type(cmd[1])}')
                except IndexError:
                    raise TBotException(code=7,
                                        return_message=f'Отсутствует сохраненный стих. Нажми на гадание еще разок',
                                        chat_id=request.chat_id)
                return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def get_statistic(self, request: LoaderRequest) -> LoaderResponse:
        """
        Get statistic
        :param request: command string
        :return: statistic
        """
        resp = LoaderResponse()
        lst = request.text.split()
        lst = [word.lower() for word in lst]
        try:
            if config.USE_DB:
                if len(lst) == 1:
                    resp.text = 'Выберите тип статистики'
                    resp.markup = custom_markup(
                        command='statistic',
                        category=['Count', 'Functions'],
                        smile='📋'
                    )
                    resp.is_extra_log = False
                    return resp
                elif len(lst) == 2:
                    if lst[1].lower() not in ('count', 'functions'):
                        raise TBotException(code=6, return_message=f'Неправильное значение параметра: {lst[1]}')
                    resp.text = 'Выберите интервал'
                    resp.markup = custom_markup(
                        command='statistic',
                        category=['Today', 'Week', 'Month', 'All'],
                        subcommands=[lst[1]],
                        smile='📋')
                    resp.is_extra_log = False
                    return resp
                interval_map = {'today': 1,
                                'week': 7,
                                'month': 30,
                                'all': 100000}
                if lst[2] not in interval_map.keys():
                    raise TBotException(code=6, return_message=f'Неправильное значение параметра: {lst[2]}')
                interval = datetime.datetime.now() - datetime.timedelta(days=interval_map[lst[2]])
                if lst[1] == 'count':
                    if lst[2] != 'today':
                        plot_data = md.LogRequests.query.with_entities(
                            cast(md.LogRequests.date_ins, Date),
                            func.count(md.LogRequests.chat_id)
                        ).filter(
                            md.LogRequests.date_ins >= interval,
                            md.LogRequests.action.is_not(None),
                            md.LogRequests.action != 'hello'
                        ).group_by(
                            cast(md.LogRequests.date_ins, Date)
                        ).all()
                        dt = []
                        cnt = []
                        for cur in plot_data:
                            dt.append(cur[0])
                            cnt.append(cur[1])
                        bgi = BaseGraphInfo(
                            'Statistic',
                            'statistic',
                            [
                                BaseSubGraphInfo(
                                    'plot', None, 'blue', 'Date', 'Count', dt, cnt
                                )
                            ]
                        )
                        resp.photo = Graph.get_base_graph(bgi)
                    to_sort = md.LogRequests.query.join(
                        md.Users,
                        md.LogRequests.chat_id == md.Users.chat_id
                    ).filter(
                        md.LogRequests.date_ins >= interval,
                        md.LogRequests.action.is_not(None),
                        md.LogRequests.action != 'hello'
                    ).with_entities(
                        func.count(md.Users.chat_id),
                        md.Users.login,
                        md.Users.first_name
                    ).group_by(
                        md.Users.chat_id
                    ).order_by(
                        desc(func.count(md.Users.chat_id))
                    ).all()
                    resp.text = ''
                    for cur in to_sort:
                        resp.text += ' '.join([str(i) for i in cur]) + '\n'
                    return resp
                elif lst[1] == 'functions':
                    bar_data = md.LogRequests.query.with_entities(
                        md.LogRequests.action,
                        func.count(md.LogRequests.action)
                    ).filter(
                        md.LogRequests.date_ins >= interval,
                        md.LogRequests.action.is_not(None),
                        md.LogRequests.action != 'hello'
                    ).group_by(
                        md.LogRequests.action
                    ).order_by(
                        desc(func.count(md.LogRequests.action))
                    ).all()
                    func_name = []
                    cnt = []
                    for cur in bar_data:
                        func_name.append(cur[0])
                        cnt.append(cur[1])
                    subbars = []
                    if len(func_name) > 10:
                        index = 10
                        while func_name:
                            subbars.append(
                                BaseSubGraphInfo(
                                    'bar',
                                    None,
                                    'green',
                                    'Name of function',
                                    'Count of requests',
                                    func_name[:index],
                                    cnt[:index]
                                )
                            )
                            func_name = func_name[index:]
                            cnt = cnt[index:]
                            index = 10 if len(func_name) > 10 else len(func_name)
                    bgi = BaseGraphInfo(
                        'Statistic',
                        'statistic',
                        subbars or [
                            BaseSubGraphInfo(
                                'bar', None, 'green', 'Name of function', 'Count of requests', func_name, cnt
                            )
                        ]
                    )
                    resp.photo = Graph.get_base_graph(bgi)
                    return resp
            else:
                raise TBotException(code=3, return_message='Нет подключения к БД')
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()
