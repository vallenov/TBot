import logging
import traceback
from mysql.connector import connect, Error

from loaders.loader import Loader

logger = logging.getLogger(__name__)
handler = logging.FileHandler('run.log')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class DBLoader(Loader):

    def __init__(self, name):
        super().__init__(name)
        self.db_name = 'TBot'
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
            self.user_privileges = {}
        self._get_privileges()

    def _get_privileges(self):
        with self.connection.cursor() as cursor:
            query = f'select chat_id, value from ' \
                    f'{self.db_name}.users u ' \
                    f'join {self.db_name}.lib_privileges p ' \
                    f'on u.privileges_id = p.p_id;'
            cursor.execute(query)
            Loader.user_privileges = {}
            for cur in cursor:
                Loader.user_privileges[cur[0]] = cur[1]
