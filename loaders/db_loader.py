import logging
import traceback
from mysql.connector import connect, Error

from loaders.loader import Loader, check_permission

logger = logging.getLogger(__name__)
handler = logging.FileHandler('run.log')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class DBLoader(Loader):

    def __init__(self, name):
        super().__init__(name)
        self.db_name = 'TBot'
        if int(self.config['MAIN']['PROD']):
            self.get_connect()
            self.get_users_fom_db()
        else:
            self.get_users_fom_config()

    def get_connect(self):
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

    def get_users_fom_db(self):
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
        logger.info('add_user')
        login_db = 'NULL' if login is None else f"'{login}'"
        first_name_db = 'NULL' if first_name is None else f"'{first_name}'"
        user_id_db = f"'{user_id}'"
        if int(self.config['MAIN']['PROD']):
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
        resp = {}
        logger.info('update_user')
        lst = text.split()
        if len(lst) != 3:
            logger.error(f'Not valid data')
            return Loader.error_resp(f'Not valid data')
        else:
            user_id = lst[1]
            if user_id not in Loader.users.keys():
                return Loader.error_resp('User not found')
            user_id_db = f"'{user_id}'"
            privileges = int(lst[2])
        if int(self.config['MAIN']['PROD']):
            with self.connection.cursor() as cursor:
                logger.info(f'Updating DB')
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
    def show_users(self, **kwargs):
        resp = {}
        logger.info('show_users')
        cnt = 1
        for key, value in Loader.users.items():
            if value['value'] > Loader.privileges_levels['regular']:
                continue
            resp[cnt] = f"Chat_id: {key}, " \
                        f"login: {value['login']}, " \
                        f"first_name: {value['first_name']}, " \
                        f"priviliges: {value['value']}"
            cnt += 1
        if not len(resp):
            resp[0] = 'Users not found'
        resp['res'] = 'OK'
        return resp

