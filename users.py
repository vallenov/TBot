from models import Users as UsersModel
from loggers import get_logger
from exceptions import TBotException

logger = get_logger(__name__)


class User:
    def __init__(self, chat_id: str, login: str, first_name: str, privileges: int, description: str):
        self.chat_id = chat_id
        self.login = login
        self.first_name = first_name
        self.privileges = privileges
        self.description = description
        self.cache = None

    def as_dict(self):
        return {
            'chat_id': self.chat_id,
            'login': self.login,
            'first_name': self.first_name,
            'privileges': self.privileges,
            'description': self.description
        }


class Users:
    def __init__(self):
        self._users = {}

    def __call__(self, user_id=None) -> dict or UsersModel:
        if not user_id:
            return self._users.values()
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
                elif isinstance(user, UsersModel):
                    chat_id = user.chat_id
                    login = user.login
                    first_name = user.first_name
                    privileges = user.value
                    description = user.description
                else:
                    raise TBotException(code=6, message=f'Bad type of user: {type(user)}')
                self.add_user(chat_id, login, first_name, privileges, description)
        else:
            raise TBotException(code=6, message=f'Input data is empty')

    def add_user(self, chat_id: str, login: str, first_name: str, privileges: int, description: str):
        self._users[chat_id] = User(chat_id, login, first_name, privileges, description)

    def __contains__(self, item):
        return True if item in self._users.keys() else False


tbot_users = Users()
