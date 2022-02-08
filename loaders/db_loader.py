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
        self.get_connect()
        self.get_privileges()

    def get_connect(self):
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

    def get_privileges(self):
        with self.connection.cursor() as cursor:
            query = f'select chat_id, value from ' \
                    f'{self.db_name}.users u ' \
                    f'join {self.db_name}.lib_privileges p ' \
                    f'on u.privileges_id = p.p_id;'
            cursor.execute(query)
            #Loader.user_privileges = {}
            for cur in cursor:
                print(cur[0], type(cur[0]), cur[1], type(cur[1]))
                Loader.user_privileges[cur[0]] = cur[1]
            print('Pr change', Loader.user_privileges)

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
        print(user_id, privileges, login, first_name)
        login_db = 'NULL' if login is None else f"'{login}'"
        first_name_db = 'NULL' if login is None else f"'{first_name}'"
        user_id_db = f"'{user_id}'"
        with self.connection.cursor() as cursor:
            p_id = self.get_p_id(privileges)
            query = f'insert into {self.db_name}.users ' \
                    f'(login, first_name, chat_id, privileges_id) ' \
                    f'values ' \
                    f"({login_db}, {first_name_db}, {user_id_db}, {p_id})"
            cursor.execute(query)
            self.connection.commit()
            logger.info(f'User {user_id} added')
            Loader.user_privileges[user_id] = privileges
            return True

    @check_permission(needed_level='root')
    def update_user(self, text: str, **kwargs):
        resp = {}
        lst = text.split()
        if len(lst) != 3:
            logger.error(f'Not valid data')
            return Loader.error_resp(f'Not valid data')
        else:
            user_id = lst[1]
            if user_id not in Loader.user_privileges.keys():
                return Loader.error_resp('User not found')
            user_id_db = f"'{user_id}'"
            privileges = int(lst[2])
        with self.connection.cursor() as cursor:
            p_id = self.get_p_id(privileges)
            query = f'update {self.db_name}.users ' \
                    f'set privileges_id = {p_id} ' \
                    f'where chat_id = {user_id_db} '
            resp[0] = f'User {user_id} updated'
            cursor.execute(query)
            self.connection.commit()
        Loader.user_privileges[user_id] = privileges
        resp['res'] = 'OK'
        return resp
