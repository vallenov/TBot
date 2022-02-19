import logging
import random
import time
import traceback
from mysql.connector import connect, Error
import threading

from loaders.loader import Loader, check_permission

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
            time.sleep(60*60)

    def get_users_fom_db(self):
        """
        Get all users' information from DB to memory
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

    def get_p_id(self, privileges: int) -> int or None:
        """
        Get privileges id by privileges value
        """
        with self.connection.cursor() as cursor:
            query = f'select t.p_id from {self.db_name}.lib_privileges t where t.value = {privileges}'
            cursor.execute(query)
            for cur in cursor:
                p_id = cur[0]
                break
            if not p_id:
                logger.error(f'p_id not found')
                return None
            else:
                return p_id

    def add_user(self, user_id: str, privileges: int, login: str, first_name: str):
        """
        Add new user to DB and memory
        """
        logger.info('add_user')
        login_db = 'NULL' if login is None else f"'{login}'"
        first_name_db = 'NULL' if first_name is None else f"'{first_name}'"
        user_id_db = f"'{user_id}'"
        if self.use_db:
            with self.connection.cursor() as cursor:
                p_id = self.get_p_id(privileges)
                query = f'insert into {self.db_name}.users ' \
                        f'(login, first_name, chat_id, privileges_id) ' \
                        f'values ' \
                        f"({login_db}, {first_name_db}, {user_id_db}, {p_id})"
                cursor.execute(query)
                self.connection.commit()
        logger.info(f'New user {user_id} added')
        Loader.users[user_id] = dict()
        Loader.users[user_id]['login'] = login
        Loader.users[user_id]['first_name'] = first_name
        Loader.users[user_id]['value'] = privileges

    @check_permission(needed_level='root')
    def update_user(self, text: str, **kwargs):
        """
        Update user privileges in DB and memory
        """
        resp = {}
        logger.info('update_user')
        lst = text.split()
        if len(lst) != 3:
            logger.error(f'Not valid data')
            return Loader.error_resp(f'Not valid data')
        else:
            user_id = lst[1]
            user_inf = Loader.users.keys()
            if all([user_id.lower() not in list(map(lambda x: x.lower(), user_inf)),
                    user_id.lower() not in list(map(lambda x: Loader.users[x]['login'].lower()
                        if Loader.users[x]['login'] is not None
                        else Loader.users[x]['login'], user_inf)),
                    user_id.lower() not in list(map(lambda x: Loader.users[x]['first_name'].lower()
                        if Loader.users[x]['first_name'] is not None
                        else Loader.users[x]['first_name'], user_inf))]):
                return Loader.error_resp('User not found')
            user_id_db = f"'{user_id}'"
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
                    user_id = cid[0]
                    user_id_db = f"'{user_id}'"
                    cnt += 1
                if cnt > 1:
                    return Loader.error_resp('Count of founded data greater then 1')
            with self.connection.cursor() as cursor:
                p_id = self.get_p_id(privileges)
                query = f'update {self.db_name}.users ' \
                        f'set privileges_id = {p_id} ' \
                        f'where chat_id = {user_id_db} '
                resp[0] = f'User {user_id} updated'
                cursor.execute(query)
                self.connection.commit()
        logger.info(f'Updating memory')
        Loader.users[user_id]['value'] = privileges
        logger.info(f'User {user_id} updated')
        resp['res'] = 'OK'
        return resp

    @check_permission(needed_level='root')
    def delete_user(self, text: str, **kwargs):
        """
        Delete user from DB and memory
        """
        resp = {}
        logger.info('delete_user')
        lst = text.split()
        if len(lst) != 2:
            logger.error(f'Not valid data')
            return Loader.error_resp(f'Not valid data')
        else:
            user_id = lst[1]
            if user_id not in Loader.users.keys():
                return Loader.error_resp('User not found')
            if Loader.users[user_id]['value'] >= Loader.privileges_levels['root']:
                return Loader.error_resp('Can not delete root users')
            user_id_db = f"'{user_id}'"
        if self.use_db:
            with self.connection.cursor() as cursor:
                logger.info(f'Updating DB')
                query = f'delete from {self.db_name}.users ' \
                        f'where chat_id = {user_id_db} '
                cursor.execute(query)
                self.connection.commit()
        logger.info(f'Updating memory')
        Loader.users.pop(user_id)
        resp[0] = f'User {user_id} deleted'
        logger.info(f'User {user_id} deleted')
        resp['res'] = 'OK'
        return resp

    @check_permission(needed_level='root')
    def show_users(self, **kwargs):
        """
        Show current users information
        """
        resp = {}
        logger.info('show_users')
        cnt = 1
        for key, value in Loader.users.items():
            if value['value'] > Loader.privileges_levels['trusted']:
                continue
            resp[cnt] = f"Chat_id: {key}, " \
                        f"login: {value['login']}, " \
                        f"first_name: {value['first_name']}, " \
                        f"privileges: {value['value']}"
            cnt += 1
        if not len(resp):
            resp[0] = 'Users not found'
        resp['res'] = 'OK'
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
            print(cnt, p)
            author = p['author']
            name = p['name'].replace("'", '"')
            text = p['text'].replace("'", "''")
            lst.append((author, name, text))
            cnt += 1
        with self.connection.cursor() as cursor:
            logger.info('Upload to DB')
            query = "insert into TBot.tmp (author, name, text) values (%s, %s, %s)"
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
        logger.info('get_poem')
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
                    random_poem = random.randint(min_id, max_id+1)
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
