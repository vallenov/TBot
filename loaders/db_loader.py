import random
import os
import datetime
import matplotlib.pyplot as plt
from mysql.connector.errors import OperationalError

import config

from loaders.loader import Loader, check_permission
from helpers import dict_to_str
import models as md
from sqlalchemy import cast, Date, exc
from sqlalchemy.sql import func
from extentions import db
from markup import custom_markup
from send_service import send_dev_message
from loggers import get_logger

logger = get_logger(__name__)


class DBLoader(Loader):
    """
    Work with DB
    """

    def __init__(self, name):
        super().__init__(name)
        if config.USE_DB:
            self.get_users_fom_db()
            logger.info('Connection to DB success')
        else:
            self.get_users_fom_config()
            logger.info('Load from config success')

    @staticmethod
    def get_users_fom_db():
        """
        Get all users' information from DB to memory
        """
        logger.info('get_users_fom_db')
        try:
            users = md.Users.query \
                .join(md.LibPrivileges, md.Users.privileges_id == md.LibPrivileges.p_id) \
                .add_columns(md.Users.chat_id,
                             md.Users.login,
                             md.Users.first_name,
                             md.LibPrivileges.value,
                             md.Users.description) \
                .all()
        except exc.DatabaseError:
            logger.info('Error connection to DB')
            send_dev_message(data={'text': f'Ошибка подключения к БД'}, by='telegram')
            exit()
        for user in users:
            user_data = dict()
            user_data['login'] = user.login
            user_data['first_name'] = user.first_name
            user_data['value'] = user.value
            user_data['description'] = user.description
            Loader.users[user.chat_id] = user_data

    @staticmethod
    def get_users_fom_config():
        """
        Get all users' information from config to memory
        """
        logger.info('get_users_fom_config')
        users = config.USERS
        for value in users.values():
            Loader.users[value['chat_id']] = {
                'login': value['login'],
                'first_name': value['first_name'],
                'value': value['privileges']
            }

    @staticmethod
    def get_p_id(privileges: int) -> int or None:
        """
        Get privileges id by privileges value
        """
        data = md.LibPrivileges.query.filter(
            md.LibPrivileges.value == privileges
        ).one_or_none()
        if not data:
            logger.error(f'p_id not found')
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
        except OperationalError:
            logger.exception('DB connection error')
            send_data = dict()
            send_data['subject'] = 'DB connection error'
            send_data['text'] = f'Reconnect to DB'
            send_dev_message(data=send_data, by='telegram')

    def add_user(self, chat_id: str, privileges: int, login: str, first_name: str):
        """
        Add new user to DB and memory
        """
        logger.info('add_user')
        if config.USE_DB:
            p_id = self.get_p_id(privileges)
            db.session.add(md.Users(chat_id=chat_id,
                                    login=login,
                                    first_name=first_name,
                                    privileges_id=p_id))
            db.session.commit()
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
    def update_user_privileges(self, text: str, **kwargs) -> dict:
        """
        Update user privileges in DB and memory
        """
        resp = {}
        lst = text.split()
        if len(lst) != 3:
            logger.error(f'Not valid data')
            return Loader.error_resp(f'Not valid data')
        else:
            chat_id = lst[1]
            user_inf = Loader.users.keys()
            if all([chat_id.lower() not in list(map(lambda x: x.lower(), user_inf)),
                    chat_id.lower() not in list(map(lambda x: Loader.users[x]['login'].lower()
                    if Loader.users[x]['login'] is not None
                    else Loader.users[x]['login'], user_inf)),
                    chat_id.lower() not in list(map(lambda x: Loader.users[x]['first_name'].lower()
                    if Loader.users[x]['first_name'] is not None
                    else Loader.users[x]['first_name'], user_inf))]):
                return Loader.error_resp('User not found')
            privileges = int(lst[2])
        if config.USE_DB:
            user = md.Users.query.filter(
                (md.Users.chat_id == chat_id) |
                (md.Users.login == chat_id) |
                (md.Users.first_name == chat_id)
            ).all()
            if len(user) > 1:
                return Loader.error_resp('Count of founded data greater then 1')
            p_id = self.get_p_id(privileges)
            for u in user:
                u.privileges_id = p_id
            db.session.commit()
        logger.info(f'Updating memory')
        Loader.users[chat_id]['value'] = privileges
        logger.info(f'User {chat_id} updated')
        resp['text'] = f'User {chat_id} updated'
        return resp

    @check_permission(needed_level='root')
    def show_users(self, **kwargs) -> dict:
        """
        Show current users information
        """
        resp = {}
        cnt = 1
        users = {}
        max_rows_lens = [0] * 5
        users[0] = 'chat_id login first_name privileges'
        for key, value in Loader.users.items():
            if value['value'] > Loader.privileges_levels['trusted']:
                continue
            users[cnt] = f"{key} " \
                         f"{value['login']} " \
                         f"{value['first_name']} " \
                         f"{value['value']}"
            cur_rows_lens = list(map(lambda x: len(x), users[cnt].split()))
            max_rows_lens[1] = cur_rows_lens[0] if cur_rows_lens[0] > max_rows_lens[1] else max_rows_lens[1]
            max_rows_lens[2] = cur_rows_lens[1] if cur_rows_lens[1] > max_rows_lens[2] else max_rows_lens[2]
            max_rows_lens[3] = cur_rows_lens[2] if cur_rows_lens[2] > max_rows_lens[3] else max_rows_lens[3]
            max_rows_lens[4] = cur_rows_lens[3] if cur_rows_lens[3] > max_rows_lens[4] else max_rows_lens[4]
            cnt += 1
        if not len(users):
            resp['text'] = Loader.error_resp('Users not found')
        else:
            for key, value in users.items():
                usr_split = users[key].split()
                for usr in range(len(usr_split)):
                    usr_split[usr] = usr_split[usr].center(max_rows_lens[usr + 1] + 1)
                users[key] = ' '.join(usr_split)
            resp['text'] = dict_to_str(users, '')
        return resp

    def _poems_to_db(self, poems: list):
        """
        Upload poems list to DB
        :param poems: [{'author': 'some', 'name': 'some', 'text': 'some'}..,
        {'author': 'some', 'name': 'some', 'text': 'some'}
        :return:
        """
        cnt = 1
        lst = []
        logger.info('Preparing to upload')
        for p in poems:
            author = p['author']
            name = p['name'].replace("'", '"')
            text = p['text'].replace("'", "''")
            lst.append((author, name, text))
            cnt += 1
        with self.connection.cursor() as cursor:
            logger.info('Upload to DB')
            query = f"insert into TBot.tmp (author, name, text) values (%s, %s, %s)"
            cursor.executemany(query, lst)
            self.connection.commit()
            logger.info('Upload complete')

    @check_permission(needed_level='root')
    def send_other(self, text: str, **kwargs):
        """
        Send message to other user
        :param text: string "command chat_id message"
        :return: dict {'chat_id': 1234567, 'text': 'some'}
        """
        resp = {}
        lst = text.split()
        if len(lst) != 3:
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
                max_id = db.session.query(func.max(md.Poems.p_id)).scalar()
                min_id = db.session.query(func.min(md.Poems.p_id)).scalar()
                random_id = random.randint(min_id, max_id + 1)
                poem = md.Poems.query.filter(
                    md.Poems.p_id == random_id
                ).one_or_none()
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
            stat_data = md.LogRequests.query \
                .join(md.Users, md.LogRequests.chat_id == md.Users.chat_id) \
                .filter(md.LogRequests.date_ins >= interval) \
                .with_entities(func.count(md.Users.chat_id), md.Users.login, md.Users.first_name) \
                .group_by(md.Users.chat_id) \
                .all()
            to_sort = []
            for cur in stat_data:
                to_sort.append([cur[0], cur[1], cur[2]])
            for index_i in range(len(to_sort)):
                for index_j in range(len(to_sort) - 1):
                    if index_i == index_j:
                        continue
                    elif to_sort[index_j][0] < to_sort[index_j + 1][0]:
                        to_sort[index_j], to_sort[index_j + 1] = to_sort[index_j + 1], to_sort[index_j]
            for cur in to_sort:
                resp['text'] += f'{cur[0]} {cur[1]} {cur[2]}\n'
            return resp
        else:
            return Loader.error_resp('DB is not used')
