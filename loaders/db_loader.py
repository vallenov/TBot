import random
import datetime
from mysql.connector.errors import OperationalError
import traceback

import config

from loaders.loader import Loader, check_permission
from helpers import dict_to_str, cut_commands
import models as md
from sqlalchemy import cast, Date, exc
from sqlalchemy.sql import func
from extentions import db
from markup import custom_markup
from send_service import send_dev_message
from loggers import get_logger
from exceptions import TBotException
from graph import Graph, BaseGraphInfo, BaseSubGraphInfo

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
                .join(md.LibPrivileges, md.Users.privileges_id == md.LibPrivileges.p_id) \
                .add_columns(md.Users.chat_id,
                             md.Users.login,
                             md.Users.first_name,
                             md.LibPrivileges.value,
                             md.Users.description) \
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
        for user in users:
            user_data = dict()
            user_data['login'] = user.login
            user_data['first_name'] = user.first_name
            user_data['value'] = user.value
            user_data['description'] = user.description
            Loader.users[user.chat_id] = user_data

    @staticmethod
    def get_users_from_config() -> None:
        """
        Get all users' information from config to memory
        """
        logger.info('get_users_fom_config')
        try:
            if not config.USERS:
                raise TBotException(code=4, message='USERS')
            for value in config.USERS.values():
                Loader.users[value['chat_id']] = {
                    'login': value['login'],
                    'first_name': value['first_name'],
                    'value': value['privileges'],
                    'description': value['description']
                }
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            exit()

    @staticmethod
    def get_p_id(privileges: int) -> int or None:
        """
        Get privileges id by privileges value
        """
        try:
            data = md.LibPrivileges.query.filter(
                md.LibPrivileges.value == privileges
            ).one_or_none()
            if not data:
                raise TBotException(code=3, message=f'Привилегия {privileges} не найдена')
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return None
        else:
            return data.p_id

    @staticmethod
    def log_request(chat_id: str) -> None:
        """
        Insert base request info to DB
        :param chat_id: person chat_id
        :return:
        """
        try:
            db.session.add(md.LogRequests(chat_id=chat_id))
            db.session.commit()
        except (OperationalError, exc.OperationalError) as e:
            logger.exception(f'DB connection error: {e}')
            raise

    def add_user(self, chat_id: str, privileges: int, login: str, first_name: str) -> None:
        """
        Add new user to DB and memory
        """
        logger.info('add_user')
        try:
            if config.USE_DB:
                p_id = self.get_p_id(privileges)
                db.session.add(md.Users(chat_id=chat_id,
                                        login=login,
                                        first_name=first_name,
                                        privileges_id=p_id))
                db.session.commit()
        except (OperationalError, exc.OperationalError) as e:
            logger.exception(f'DB connection error: {e}')
            raise
        logger.info(f'New user {chat_id} added')
        Loader.users[chat_id] = dict()
        Loader.users[chat_id]['login'] = login
        Loader.users[chat_id]['first_name'] = first_name
        Loader.users[chat_id]['value'] = privileges

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
        Loader.users[chat_id]['login'] = login
        Loader.users[chat_id]['first_name'] = first_name
        logger.info('User info updated')

    @check_permission(needed_level='root')
    def update_user_data(self, text: str, **kwargs) -> dict:
        """
        Update user privileges in DB and memory
        """
        resp = {}
        cmd = text.split()
        cmd = [word.lower() for word in cmd]
        try:
            if len(cmd) < 4:
                raise TBotException(code=6,
                                    return_message=f'Неправильное количество параметров: {len(cmd)}',
                                    parameres_count=len(cmd))
            else:
                chat_id = cmd[2]
                if cmd[1] == 'description':
                    new_value = ' '.join(cmd[3:])
                elif cmd[1] == 'privileges':
                    new_value = int(cmd[3])
                else:
                    raise TBotException(code=6,
                                        return_message=f'Неправильное значение параметра: {cmd[1]}',
                                        parameres_value=cmd[2])
            if config.USE_DB:
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
                    new_value = self.get_p_id(new_value)
                for u in user:
                    chat_id = u.chat_id
                    if cmd[1] == 'description':
                        u.description = new_value
                    if cmd[1] == 'privileges':
                        u.privileges_id = new_value
                db.session.commit()
                logger.info(f'Updating memory')
                if cmd[1] == 'privileges':
                    Loader.users[chat_id]['value'] = int(cmd[3])
                if cmd[1] == 'description':
                    Loader.users[chat_id]['description'] = new_value
                logger.info(f'User {chat_id} {cmd[1]} updated')
                resp['text'] = f'User {chat_id} {cmd[1]} updated'
                return resp
            else:
                raise TBotException(code=3, return_message='Нет подключения к БД')
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def show_users(self, **kwargs) -> dict:
        """
        Show current users information
        """
        resp = {}
        cnt = 1
        users = dict()
        users[0] = ['chat_id', 'login', 'first_name', 'privileges', 'description']
        max_rows_lens = [0] + list(map(lambda x: len(x), users[0]))
        try:
            for key, value in Loader.users.items():
                if value['value'] > Loader.privileges_levels['trusted']:
                    continue
                users[cnt] = [key, value['login'], value['first_name'], str(value['value']), value['description']]
                cur_rows_lens = list(map(lambda x: 0 if not x else len(x), users[cnt]))
                for i in range(1, 6):
                    max_rows_lens[i] = cur_rows_lens[i-1] if cur_rows_lens[i-1] > max_rows_lens[i] else max_rows_lens[i]
                cnt += 1
            if not len(users):
                raise TBotException(code=3, return_message='Пользователь не найден')
            else:
                for key, value in users.items():
                    tmp = ''
                    for usr in range(len(users[key])):
                        item = users[key][usr] or 'None'
                        tmp += item.center(max_rows_lens[usr+1] + 3)
                    users[key] = tmp
                resp['text'] = dict_to_str(users, '')
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def send_other(self, text: str, **kwargs) -> dict:
        """
        Send message to other user
        :param text: string "command chat_id message"
        :return: dict {'chat_id': 1234567, 'text': 'some'}
        """
        resp = {}
        lst = text.split()
        try:
            if len(lst) < 3:
                raise TBotException(code=6, return_message=f'Неправильное количество параметров: {len(lst)}')
            try:
                chat_id = int(lst[1])
            except ValueError:
                raise TBotException(code=6, return_message=f'Неправильное значение параметра: {lst[1]}')
            if str(chat_id) not in Loader.users.keys():
                raise TBotException(code=3, return_message=f'Пользователь {lst[1]} не найден')
            resp['chat_id'] = chat_id
            resp['text'] = cut_commands(text, 2)
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def send_to_all_users(self, text: str, **kwargs):
        """
        Send message to all users
        :param text: string "command chat_id message"
        :return: dict {'chat_id': [1234567, 4637499], 'text': 'some'}
        """
        resp = {}
        lst = text.split()
        try:
            if len(lst) < 2:
                raise TBotException(code=6, return_message=f'Неправильное количество параметров: {len(lst)}')
            resp['chat_id'] = []
            for chat_id in Loader.users.keys():
                try:
                    chat_id = int(chat_id)
                except ValueError:
                    logger.exception(f'Chat {chat_id} is not convert to int')
                resp['chat_id'].append(chat_id)
            resp['text'] = cut_commands(text, 1)
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission()
    def send_to_admin(self, text: str, **kwargs):
        """
        Send message to admin
        :param text: string "command chat_id message"
        :return: dict {'chat_id': admin_id, 'text': 'some'}
        """
        resp = {}
        lst = text.split()
        try:
            if len(lst) < 2:
                raise TBotException(code=6, return_message=f'Неправильное количество параметров: {len(lst)}')
            resp['chat_id'] = int(config.USERS['root_id']['chat_id'])
            resp['text'] = str(f"Message from {Loader.users[kwargs['chat_id']]['first_name'] or kwargs['chat_id']}\n"
                               f"Text: {cut_commands(text, 1)}")
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
    def get_poem(self, text: str, **kwargs) -> dict:
        """
        Get poem from DB
        :param:
        :return: poesy string
        """
        resp = {}
        try:
            if config.USE_DB:
                lst = text.split()
                if len(lst) == 1:
                    poem = self._get_random_poem()
                    if not poem:
                        raise TBotException(code=3, message='Стих не найден')
                else:
                    search_string = ' '.join(lst[1:])
                    poems = md.Poems.query.filter(
                        md.Poems.author.like(f'%{search_string}%') | md.Poems.name.like(f'%{search_string}%')
                    ).all()
                    if poems:
                        poem = random.choice(poems)
                    else:
                        raise TBotException(code=3, message='Стих не найден')
                resp['text'] = f"{poem.author}\n\n{poem.name}\n\n{poem.text}"
                return resp
            else:
                raise TBotException(code=3, return_message='Нет подключения к БД')
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission()
    def poem_divination(self, text: str, **kwargs):
        """
        Poem divination
        """
        resp = {}
        try:
            cmd = text.split()
            if kwargs['chat_id'] not in Loader.users.keys():
                raise TBotException(code=3, message=f'User {kwargs["chat_id"]} not found')
            if not Loader.users[kwargs['chat_id']].get('cache'):
                Loader.users[kwargs['chat_id']]['cache'] = dict()
            if len(cmd) == 1:
                if 'poem' in Loader.users[kwargs['chat_id']]['cache']:
                    Loader.users[kwargs['chat_id']]['cache'].pop('poem')
                if not Loader.users[kwargs['chat_id']]['cache'].get('poem'):
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
                    Loader.users[kwargs['chat_id']]['cache']['poem'] = poem
                    resp['text'] = 'Выберите четверостишие'
                    resp['markup'] = custom_markup('divination', [str(i) for i in range(1, count_of_quatrains + 1)],
                                                   '🔮')
                    return resp
            else:
                poem = Loader.users[kwargs['chat_id']]['cache'].get('poem')
                if not poem:
                    raise TBotException(code=7,
                                        return_message=f'Отсутствует сохраненный стих. Нажми на гадание еще разок',
                                        chat_id=kwargs.get('chat_id'),
                                        cache_field='poem')
                quatrains = poem.text.split('\n\n')
                cmd = text.split()
                try:
                    number_of_quatrain = int(cmd[1])
                    resp['text'] = quatrains[number_of_quatrain - 1]
                except ValueError:
                    raise TBotException(code=6,
                                        message='Неправильный тип параметра',
                                        parameter=cmd[1],
                                        type=type(cmd[1]))
                except IndexError:
                    raise TBotException(code=7,
                                        return_message=f'Отсутствует сохраненный стих. Нажми на гадание еще разок',
                                        chat_id=kwargs.get('chat_id'),
                                        cache_field='poem')
                return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def get_statistic(self, text, **kwargs) -> dict:
        """
        Get statistic
        :param text: command string
        :return: statistic
        """
        resp = {'text': ''}
        lst = text.split()
        lst = [word.lower() for word in lst]
        try:
            if config.USE_DB:
                if len(lst) == 1:
                    resp['text'] = 'Выберите интервал'
                    resp['markup'] = custom_markup('statistic',
                                                   ['Today', 'Week', 'Month', 'All'],
                                                   '📋')
                    return resp
                interval_map = {'today': 1,
                                'week': 7,
                                'month': 30,
                                'all': 100000}
                if lst[1] not in interval_map.keys():
                    raise TBotException(code=6, return_message=f'Wrong parameter value: {lst[1]}')
                interval = datetime.datetime.now() - datetime.timedelta(days=interval_map[lst[1]])
                if lst[1] != 'today':
                    plot_data = md.LogRequests.query \
                        .with_entities(cast(md.LogRequests.date_ins, Date), func.count(md.LogRequests.chat_id)) \
                        .group_by(cast(md.LogRequests.date_ins, Date)) \
                        .filter(md.LogRequests.date_ins >= interval) \
                        .all()
                    dt = []
                    cnt = []
                    for cur in plot_data:
                        dt.append(cur[0])
                        cnt.append(cur[1])
                    bgi = BaseGraphInfo('Statistic', 'statistic', [
                        BaseSubGraphInfo('plot', None, 'blue', 'Date', 'Count', dt, cnt)])
                    resp['photo'] = Graph.get_base_graph(bgi)
                to_sort = md.LogRequests.query \
                    .join(md.Users, md.LogRequests.chat_id == md.Users.chat_id) \
                    .filter(md.LogRequests.date_ins >= interval) \
                    .with_entities(func.count(md.Users.chat_id), md.Users.login, md.Users.first_name) \
                    .group_by(md.Users.chat_id) \
                    .all()
                for index_i in range(len(to_sort)):
                    for index_j in range(len(to_sort) - 1):
                        if index_i == index_j:
                            continue
                        elif to_sort[index_j][0] < to_sort[index_j + 1][0]:
                            to_sort[index_j], to_sort[index_j + 1] = to_sort[index_j + 1], to_sort[index_j]
                for cur in to_sort:
                    resp['text'] += ' '.join([str(i) for i in cur]) + '\n'
                return resp
            else:
                raise TBotException(code=3, return_message='Нет подключения к БД')
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()
