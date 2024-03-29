from sqlalchemy.engine.row import Row

from loggers import get_logger
from exceptions import TBotException

logger = get_logger(__name__)


class User:
    def __init__(
            self,
            chat_id: str,
            login: str,
            first_name: str,
            privileges: int,
            description: str,
            active: bool = True
    ):
        self.chat_id = chat_id
        self.login = login
        self.first_name = first_name
        self.privileges = privileges
        self.description = description
        self.active = active
        self.cache = None

    def __repr__(self):
        return f'''(
        chat_id: {self.chat_id}, 
        login: {self.login}, 
        first_name: {self.first_name}, 
        privileges: {self.privileges}, 
        description: {self.description}, 
        action: {self.active}
        )'''

    def as_dict(self):
        return {
            'chat_id': self.chat_id,
            'login': self.login,
            'first_name': self.first_name,
            'privileges': self.privileges,
            'description': self.description,
            'active': self.active
        }


class MemUsers:
    def __init__(self):
        self._users = {}

    def __call__(self, user_id=None) -> list or User:
        if not user_id:
            return self.all()
        else:
            return self._users[user_id] if user_id in self._users.keys() else None

    def add_users(self, user_data: list):
        if len(user_data):
            for user in user_data:
                if isinstance(user, dict):
                    chat_id = user.get('chat_id')
                    login = user.get('login')
                    first_name = user.get('first_name')
                    privileges = user.get('privileges')
                    description = user.get('description')
                    active = user.get('active')
                elif isinstance(user, Row):
                    chat_id = user.chat_id
                    login = user.login
                    first_name = user.first_name
                    privileges = user.value
                    description = user.description
                    active = user.active
                else:
                    raise TBotException(code=6, message=f'Bad type of user: {type(user)}')
                self.add_user(
                    chat_id=chat_id,
                    login=login,
                    first_name=first_name,
                    privileges=privileges,
                    description=description,
                    active=active
                )
        else:
            raise TBotException(code=6, message=f'Input data is empty')

    def add_user(
            self,
            chat_id: str,
            privileges: int,
            login: str = None,
            first_name: str = None,
            description: str = None,
            active: bool = True
    ):
        self._users[chat_id] = User(
            chat_id=chat_id,
            login=login,
            first_name=first_name,
            privileges=privileges,
            description=description,
            active=active
        )

    def del_user(self, chat_id: str):
        if not chat_id:
            raise TBotException(code=2, message=f'User {chat_id} not found')
        else:
            self._users.pop(chat_id)

    def all(self):
        return self._users.values()

    def active(self):
        return list(filter(lambda u: u.active, self._users.values()))

    def __contains__(self, item):
        return True if item in self._users.keys() else False


tbot_users = MemUsers()
