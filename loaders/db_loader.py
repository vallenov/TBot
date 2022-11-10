import random
import os
import datetime
import matplotlib.pyplot as plt
from mysql.connector.errors import OperationalError

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
from exceptions import (
    ConfigAttributeNotFoundError,
    NotFoundInDatabaseError,
    WrongParameterCountError,
    WrongParameterValueError,
    UserNotFoundError,
    WrongParameterTypeError,
    EmptyCacheError,
)

logger = get_logger(__name__)


class DBLoader(Loader):
    """
    Work with DB
    """

    def __init__(self, name):
        super().__init__(name)
        if config.USE_DB:
            self.get_users_from_db()
            logger.info('Connection to DB success')
        else:
            self.get_users_from_config()
            logger.info('Load from config success')

    @staticmethod
    def get_users_from_db():
        """
        Get all users' information from DB to memory
        """
        logger.info('get_users_from_db')
        users = None
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
                raise NotFoundInDatabaseError('Users')
        except exc.DatabaseError:
            logger.info('Error connection to DB')
            send_dev_message(data={'text': f'Ошибка подключения к БД'}, by='telegram')
            exit()
        except NotFoundInDatabaseError as e:
            logger.exception(e)
            exit()
        for user in users:
            user_data = dict()
            user_data['login'] = user.login
            user_data['first_name'] = user.first_name
            user_data['value'] = user.value
            user_data['description'] = user.description
            Loader.users[user.chat_id] = user_data

    @staticmethod
    def get_users_from_config():
        """
        Get all users' information from config to memory
        """
        logger.info('get_users_fom_config')
        try:
            if not config.USERS:
                raise ConfigAttributeNotFoundError('USERS')
            for value in config.USERS.values():
                Loader.users[value['chat_id']] = {
                    'login': value['login'],
                    'first_name': value['first_name'],
                    'value': value['privileges'],
                    'description': value['description']
                }
        except ConfigAttributeNotFoundError as e:
            logger.exception(e)
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
                raise NotFoundInDatabaseError('LibPrivileges')
        except NotFoundInDatabaseError as e:
            logger.exception(e)
            return None
        else:
            return data.p_id

    @staticmethod
    def log_request(chat_id: str):
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

    def add_user(self, chat_id: str, privileges: int, login: str, first_name: str):
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
    def update_user(chat_id: str, login: str, first_name: str):
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
        valid_fields = ['description', 'privileges']
        try:
            if len(cmd) < 4:
                raise WrongParameterCountError(len(cmd))
            elif cmd[1] not in valid_fields:
                raise WrongParameterValueError(cmd[2])
            else:
                chat_id = cmd[2]
                new_value = None
                if cmd[1] == 'description':
                    new_value = ' '.join(cmd[3:])
                if cmd[1] == 'privileges':
                    new_value = int(cmd[3])
            if config.USE_DB:
                user = md.Users.query.filter(
                    (md.Users.chat_id == chat_id) |
                    (md.Users.login == chat_id) |
                    (md.Users.first_name == chat_id)
                ).all()
                if not len(user):
                    raise NotFoundInDatabaseError('users')
                if len(user) > 1:
                    return Loader.error_resp('Count of founded data greater then 1')
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
                return Loader.error_resp('DB does not using')
        except WrongParameterCountError:
            logger.error(f'Wrong count of parameters')
            return Loader.error_resp(f'Wrong count of parameters')
        except WrongParameterValueError:
            logger.error(f'Not valid parameter data')
            return Loader.error_resp(f'Not valid parameter data')
        except NotFoundInDatabaseError:
            logger.error(f'User not found')
            return Loader.error_resp('User not found')

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
        for key, value in Loader.users.items():
            if value['value'] > Loader.privileges_levels['trusted']:
                continue
            users[cnt] = [key, value['login'], value['first_name'], str(value['value']), value['description']]
            cur_rows_lens = list(map(lambda x: 0 if not x else len(x), users[cnt]))
            max_rows_lens[1] = cur_rows_lens[0] if cur_rows_lens[0] > max_rows_lens[1] else max_rows_lens[1]
            max_rows_lens[2] = cur_rows_lens[1] if cur_rows_lens[1] > max_rows_lens[2] else max_rows_lens[2]
            max_rows_lens[3] = cur_rows_lens[2] if cur_rows_lens[2] > max_rows_lens[3] else max_rows_lens[3]
            max_rows_lens[4] = cur_rows_lens[3] if cur_rows_lens[3] > max_rows_lens[4] else max_rows_lens[4]
            max_rows_lens[5] = cur_rows_lens[4] if cur_rows_lens[4] > max_rows_lens[5] else max_rows_lens[5]
            cnt += 1
        if not len(users):
            resp['text'] = Loader.error_resp('Users not found')
        else:
            for key, value in users.items():
                tmp = ''
                for usr in range(len(users[key])):
                    item = users[key][usr] or 'None'
                    tmp += item.center(max_rows_lens[usr+1] + 3)
                users[key] = tmp
            resp['text'] = dict_to_str(users, '')
        return resp

    @check_permission(needed_level='root')
    def send_other(self, text: str, **kwargs):
        """
        Send message to other user
        :param text: string "command chat_id message"
        :return: dict {'chat_id': 1234567, 'text': 'some'}
        """
        resp = {}
        lst = text.split()
        if len(lst) < 3:
            return Loader.error_resp('Format is not valid')
        try:
            chat_id = int(lst[1])
        except ValueError:
            return Loader.error_resp('Chat_id format is not valid')
        if str(chat_id) not in Loader.users.keys():
            return Loader.error_resp('User not found')
        resp['chat_id'] = chat_id
        resp['text'] = ' '.join(lst[2:])
        return resp

    @check_permission(needed_level='root')
    def send_to_all_users(self, text: str, **kwargs):
        """
        Send message to all users
        :param text: string "command chat_id message"
        :return: dict {'chat_id': [1234567, 4637499], 'text': 'some'}
        """
        resp = {}
        lst = text.split()
        if len(lst) < 3:
            return Loader.error_resp('Not enough params')
        resp['chat_id'] = []
        for chat_id in Loader.users.keys():
            try:
                chat_id = int(chat_id)
            except ValueError:
                logger.exception(f'Chat {chat_id} is not convert to int')
            resp['chat_id'].append(chat_id)
        resp['text'] = ' '.join(lst[1:])
        return resp

    @check_permission()
    def send_to_admin(self, text: str, **kwargs):
        """
        Send message to admin
        :param text: string "command chat_id message"
        :return: dict {'chat_id': admin_id, 'text': 'some'}
        """
        resp = {}
        lst = text.split()
        if len(lst) < 2:
            return Loader.error_resp('Format is not valid')
        resp['chat_id'] = int(config.USERS['root_id']['chat_id'])
        resp['text'] = f"Message from {kwargs['chat_id']}\nText: {cut_commands(text, 1)}"
        return resp

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
        if config.USE_DB:
            lst = text.split()
            if len(lst) == 1:
                poem = self._get_random_poem()
                if not poem:
                    Loader.error_resp('Something wrong')
            else:
                search_string = ' '.join(lst[1:])
                poems = md.Poems.query.filter(
                    md.Poems.author.like(f'%{search_string}%') | md.Poems.name.like(f'%{search_string}%')
                ).all()
                if poems:
                    poem = random.choice(poems)
                else:
                    return Loader.error_resp('Poem not found')
            resp['text'] = f"{poem.author}\n\n{poem.name}\n\n{poem.text}"
            return resp
        else:
            return Loader.error_resp('DB does not using')

    @check_permission()
    def poem_divination(self, text: str, **kwargs):
        """
        Poem divination
        """
        resp = {}
        try:
            cmd = text.split()
            if kwargs['chat_id'] not in Loader.users.keys():
                raise UserNotFoundError(kwargs['chat_id'])
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
                    raise EmptyCacheError('poem')
                quatrains = poem.text.split('\n\n')
                cmd = text.split()
                try:
                    number_of_quatrain = int(cmd[1])
                    resp['text'] = quatrains[number_of_quatrain - 1]
                except ValueError:
                    raise WrongParameterTypeError(cmd[1])
                except IndexError:
                    raise EmptyCacheError('poem')
                return resp
        except UserNotFoundError as e:
            logger.exception(f'Chat {e.chat_id} not found')
            return Loader.error_resp(f'Chat {e.chat_id} not found')
        except WrongParameterTypeError as e:
            logger.exception(f'Chat {e.param} not found')
            return Loader.error_resp(f'Type of param {e.param} is not valid')
        except EmptyCacheError as e:
            logger.exception(f'Empty param: {e.param}')
            return Loader.error_resp(f'Отсутствует сохраненный стих. Нажми на гадание еще разок')

    @staticmethod
    def get_graph(interval: str) -> str:
        """
        Create graph image
        :param interval: graph interval
        :return: path to image
        """
        dt = []
        cnt = []
        interval_plot = {'week': 7,
                         'month': 30,
                         'all': 10000}
        interval = datetime.datetime.now() - datetime.timedelta(days=interval_plot[interval])
        plot_data = md.LogRequests.query \
            .with_entities(cast(md.LogRequests.date_ins, Date), func.count(md.LogRequests.chat_id)) \
            .group_by(cast(md.LogRequests.date_ins, Date)) \
            .filter(md.LogRequests.date_ins >= interval) \
            .all()
        for cur in plot_data:
            dt.append(cur[0])
            cnt.append(cur[1])
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        unique_name = str(datetime.datetime.now()).replace(':', '').replace(' ', '')[:16]
        img_path = os.path.join('tmp', f'graph_{unique_name}.png')
        plt.figure(figsize=(15, 5))
        plt.plot(dt, cnt)
        plt.xlabel('Date', fontsize=14)
        plt.ylabel('Count of requests', fontsize=14)
        plt.grid()
        plt.savefig(img_path)
        plt.close()
        return img_path

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
                return Loader.error_resp('Interval is not valid')
            if lst[1] != 'today':
                resp['photo'] = DBLoader.get_graph(lst[1])
            interval = datetime.datetime.now() - datetime.timedelta(days=interval_map[lst[1]])
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
            return Loader.error_resp('DB is not used')
