import logging
import random
import time
import traceback
import os
import datetime
from mysql.connector import connect, Error
import threading
import matplotlib.pyplot as plt

from loaders.loader import Loader, check_permission
import models as md
from sqlalchemy.sql import func
from extentions import db

logger = logging.getLogger(__name__)
handler = logging.FileHandler('run.log')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class DBLoader(Loader):
    """
    Work with DB
    """

    def __init__(self, name):
        super().__init__(name)
        self.db_name = 'TBot'
        if self.use_db:
            self.get_connect()
            self.get_users_fom_db()
            cwu = threading.Thread(target=self.connection_warming_up)
            cwu.start()
        else:
            self.get_users_fom_config()

    def get_connect(self):
        """
        Initiate connection to DB
        """
        logger.info('get_connect')
        try:
            logger.info(f'Try to connect to DB')
            self.connection = connect(
                host=self.config['DB']['host'],
                user=self.config['DB']['login'],
                password=self.config['DB']['password'])
        except Error as e:
            logger.exception(f'Connection error {e}\nTraceback: {traceback.format_exc()}')
        else:
            logger.info(f'Connection to DB success')

    def connection_warming_up(self):
        """
        Periodic connection warming up
        """
        while True:
            logger.info('Connection warming up')
            with self.connection.cursor() as cursor:
                query = 'select 1 from dual'
                cursor.execute(query)
                for _ in cursor:
                    pass
            time.sleep(60 * 60)

    @staticmethod
    def get_users_fom_db():
        """
        Get all users' information from DB to memory
        """
        logger.info('get_users_fom_db')
        users = md.Users.query \
            .join(md.LibPrivileges, md.Users.privileges_id == md.LibPrivileges.p_id) \
            .add_columns(md.Users.chat_id, md.Users.login, md.Users.first_name, md.LibPrivileges.value) \
            .all()
        for user in users:
            user_data = dict()
            user_data['login'] = user.login
            user_data['first_name'] = user.first_name
            user_data['value'] = user.value
            Loader.users[user.chat_id] = user_data

    def get_users_fom_db_mysql_conn(self):
        """
        Get all users' information from DB to memory
        (don't use. use get_users_fom_db instead)
        """
        logger.info('get_users_fom_db')
        with self.connection.cursor() as cursor:
            query = f'select chat_id, login, first_name, value from ' \
                    f'{self.db_name}.users u ' \
                    f'join {self.db_name}.lib_privileges p ' \
                    f'on u.privileges_id = p.p_id;'
            cursor.execute(query)
            for cur in cursor:
                user_data = dict()
                user_data['login'] = cur[1]
                user_data['first_name'] = cur[2]
                user_data['value'] = cur[3]
                Loader.users[cur[0]] = user_data

    def get_users_fom_config(self):
        """
        Get all users' information from config to memory
        """
        logger.info('get_users_fom_config')
        users = self.config['USERS']
        for value in users.values():
            lst = value.split(',')
            user_data = dict()
            user_data['login'] = lst[1]
            user_data['first_name'] = lst[2]
            user_data['value'] = int(lst[3])
            Loader.users[lst[0]] = user_data

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
        db.session.add(md.LogRequests(chat_id=chat_id))
        db.session.commit()

    def log_request_mysql_conn(self, chat_id: str):
        """
        Insert base request info to DB
        (don't use. use log_request instead)
        :param chat_id: person chat_id
        :return:
        """
        with self.connection.cursor() as cursor:
            query = f"insert into {self.db_name}.log_requests" \
                    f"(chat_id) values ('{chat_id}')"
            cursor.execute(query)
            self.connection.commit()

    def add_user(self, chat_id: str, privileges: int, login: str, first_name: str):
        """
        Add new user to DB and memory
        """
        logger.info('add_user')
        if self.use_db:
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

    def add_user_mysql_conn(self, chat_id: str, privileges: int, login: str, first_name: str):
        """
        Add new user to DB and memory
        """
        logger.info('add_user')
        login_db = 'NULL' if login is None else f"'{login}'"
        first_name_db = 'NULL' if first_name is None else f"'{first_name}'"
        chat_id_db = f"'{chat_id}'"
        if self.use_db:
            with self.connection.cursor() as cursor:
                p_id = self.get_p_id(privileges)
                query = f'insert into {self.db_name}.users ' \
                        f'(login, first_name, chat_id, privileges_id) ' \
                        f'values ' \
                        f"({login_db}, {first_name_db}, {chat_id_db}, {p_id})"
                cursor.execute(query)
                self.connection.commit()
        logger.info(f'New user {chat_id} added')
        Loader.users[chat_id] = dict()
        Loader.users[chat_id]['login'] = login
        Loader.users[chat_id]['first_name'] = first_name
        Loader.users[chat_id]['value'] = privileges

    def update_user(self, chat_id: str, login: str, first_name: str):
        """
        Update user info in DB and memory
        :param chat_id: unique user_id
        :param login: login
        :param first_name: first_name
        """
        logger.info('update_user')
        if self.use_db:
            user = md.Users.query.filter(md.Users.chat_id == chat_id).one_or_none()
            user.login = login
            user.first_name = first_name
            db.session.commit()
        Loader.users[chat_id]['login'] = login
        Loader.users[chat_id]['first_name'] = first_name
        logger.info('User info updated')

    def update_user_mysql_conn(self, chat_id: str, login: str, first_name: str):
        """
        Update user info in DB and memory
        (don't use. use update_user instead)
        :param chat_id: unique user_id
        :param login: login
        :param first_name: first_name
        """
        logger.info('update_user')
        if self.use_db:
            with self.connection.cursor() as cursor:
                chat_id_db = f"'{chat_id}'"
                login_db = 'NULL' if not login else f"'{login}'"
                first_name_db = 'NULL' if not first_name else f"'{first_name}'"
                query = f'update {self.db_name}.users ' \
                        f'set login = {login_db}, ' \
                        f'first_name = {first_name_db} ' \
                        f'where chat_id = {chat_id_db} '
                cursor.execute(query)
                self.connection.commit()
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
        if self.use_db:
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
    def update_user_privileges_mysql_conn(self, text: str, **kwargs) -> dict:
        """
        Update user privileges in DB and memory
        (don't use. use update_user_privileges instead)
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
            user_id_db = f"'{chat_id}'"
            privileges = int(lst[2])
        if self.use_db:
            with self.connection.cursor() as cursor:
                logger.info(f'Updating DB')
                query = f'select chat_id from {self.db_name}.users ' \
                        f'where chat_id = {user_id_db} ' \
                        f'or login = {user_id_db} ' \
                        f'or first_name = {user_id_db}'
                cursor.execute(query)
                cnt = 0
                for cid in cursor:
                    chat_id = cid[0]
                    chat_id_db = f"'{chat_id}'"
                    cnt += 1
                if cnt > 1:
                    return Loader.error_resp('Count of founded data greater then 1')
            with self.connection.cursor() as cursor:
                p_id = self.get_p_id(privileges)
                query = f'update {self.db_name}.users ' \
                        f'set privileges_id = {p_id} ' \
                        f'where chat_id = {chat_id_db} '
                resp['text'] = f'User {chat_id} updated'
                cursor.execute(query)
                self.connection.commit()
        logger.info(f'Updating memory')
        Loader.users[chat_id]['value'] = privileges
        logger.info(f'User {chat_id} updated')
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
            resp['text'] = Loader.dict_to_str(users, '')
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
            query = f"insert into {self.db_name}.tmp (author, name, text) values (%s, %s, %s)"
            cursor.executemany(query, lst)
            self.connection.commit()
            logger.info('Upload complete')

    @check_permission()
    def get_poem(self, text: str, **kwargs) -> dict:
        """
        Get poem from DB
        :param:
        :return: poesy string
        """
        resp = {}
        if self.use_db:
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

    @check_permission()
    def get_poem_msql_conn(self, text: str, **kwargs) -> dict:
        """
        Get poem from DB
        (Not in use) use get_poem instead
        :param:
        :return: poesy string
        """
        resp = {}
        if self.use_db:
            lst = text.split()
            if len(lst) == 1:
                with self.connection.cursor() as cursor:
                    query = f'select min(p.p_id), max(p.p_id) from {self.db_name}.poems p'
                    cursor.execute(query)
                    for cnt in cursor:
                        min_id = int(cnt[0])
                        max_id = int(cnt[1])
                        break
                    random_poem = random.randint(min_id, max_id + 1)
                with self.connection.cursor() as cursor:
                    query = f'select * from {self.db_name}.poems p where p.p_id = {random_poem}'
                    cursor.execute(query)
                    for poem in cursor:
                        resp['text'] = f"{poem[1]}\n\n{poem[2]}\n\n{poem[3]}"
            else:
                search_string = ' '.join(lst[1:])
                with self.connection.cursor() as cursor:
                    query = f"select * from {self.db_name}.poems " \
                            f"where author like '%{search_string}%' " \
                            f"or name like '%{search_string}%'"
                    poems = []
                    cursor.execute(query)
                    for cur in cursor:
                        poems.append(cur)
                if poems:
                    poem = random.choice(poems)
                else:
                    return Loader.error_resp('Poem not found')
                resp['text'] = f"{poem[1]}\n\n{poem[2]}\n\n{poem[3]}"
            return resp
        else:
            return Loader.error_resp('DB does not using')

    def get_graph(self, interval: str) -> str:
        """
        Create graph image
        :param interval: graph interval
        :return: path to image
        """
        dt = []
        cnt = []
        interval_plot = {'week': 'where date(dc.date) > date(current_date() - interval 7 day) ',
                         'month': 'where date(dc.date) > date(current_date() - interval 30 day) '}
        with self.connection.cursor() as cursor:
            query = f"select * from (select date(lr.date_ins) date, count(*) cnt " \
                    f"from {self.db_name}.log_requests lr " \
                    f"group by date(lr.date_ins)) as dc " \
                    f"{interval_plot.get(interval, '')}"
            cursor.execute(query)
            for cur in cursor:
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
        if self.use_db:
            if len(lst) == 1:
                resp['text'] = 'Выберите интервал'
                resp['markup'] = Loader.gen_custom_markup('statistic',
                                                          ['Today', 'Week', 'Month', 'All'],
                                                          '📋')
                return resp
            # if lst[1] != 'today':
            #     resp['photo'] = self.get_graph(lst[1])
            interval = {'today': 1,
                        'week': 7,
                        'month': 30,
                        'all': ''}
            if lst[1] not in interval.keys():
                return Loader.error_resp('Interval is not valid')
            stat_data = md.LogRequests.query \
                .join(md.Users, md.LogRequests.chat_id == md.Users.chat_id) \
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

    @check_permission(needed_level='root')
    def get_statistic_mysql_conn(self, text, **kwargs) -> dict:
        """
        Get statistic
        :param text: command string
        :return: statistic
        """
        resp = {'text': ''}
        lst = text.split()
        if self.use_db:
            if len(lst) == 1:
                resp['text'] = 'Выберите интервал'
                resp['markup'] = Loader.gen_custom_markup('statistic',
                                                          ['Today', 'Week', 'Month', 'All'],
                                                          '📋')
                return resp
            if lst[1] != 'today':
                resp['photo'] = self.get_graph(lst[1])
            interval = {'today': 'where lr.date_ins > current_date() - interval 1 day ',
                        'week': 'where lr.date_ins > current_date() - interval 7 day ',
                        'month': 'where lr.date_ins > current_date() - interval 30 day ',
                        'all': ''}
            if lst[1] not in interval.keys():
                return Loader.error_resp('Interval is not valid')
            with self.connection.cursor() as cursor:
                query = f"select count(u.chat_id), u.login, u.first_name " \
                        f"from {self.db_name}.log_requests lr " \
                        f"join {self.db_name}.users u on lr.chat_id = u.chat_id " \
                        f"{interval[lst[1]]}" \
                        f"group by u.chat_id"
                cursor.execute(query)
                to_sort = []
                for cur in cursor:
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
