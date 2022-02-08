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
                print(cur[0], cur[1])
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

    @check_permission(needed_level='root')
    def update_user(self, text: str, **kwargs):
        resp = {}
        lst = text.split()
        user_id = None
        privileges = None
        login = None
        first_name = None
        if len(lst) < 3 or len(lst) > 5:
            logger.error(f'Not valid data')
            return Loader.error_resp(f'Not valid data')
        elif len(lst) == 3:
            user_id = int(lst[1])
            privileges = int(lst[2])
        else:
            user_id = int(lst[1])
            privileges = int(lst[2])
            login = lst[3]
            first_name = lst[4]
        #user_id: int, privileges: int, login: str = None, first_name: str = None
        with self.connection.cursor() as cursor:
            p_id = self.get_p_id(privileges)
            if user_id not in Loader.user_privileges.keys():
                if login is None:
                    logger.error(f'Empty login')
                    return Loader.error_resp(f'Empty login')
                query = f'insert into {self.db_name}.users ' \
                        f'(login, first_name, chat_id, privileges_id) ' \
                        f'values ' \
                        f'({login}, {first_name}, {user_id}, {p_id})'
                resp[0] = f'User {user_id} added'
            else:
                query = f'update {self.db_name}.users ' \
                        f'set privileges_id = {p_id} ' \
                        f'where chat_id = {user_id} '
                resp[0] = f'User {user_id} updated'
            cursor.execute(query)
            self.connection.commit()
        resp['res'] = 'OK'
        return resp
