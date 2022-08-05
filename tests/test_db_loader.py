from sqlalchemy import exc

from loaders.loader import Loader
from loaders.db_loader import DBLoader
from extentions import db
from TBot import TBot


class Message:
    def __init__(self, chat_id, login, first_name, msg_text):
        self.json = {'chat': {
            'id': chat_id,
            'username': login,
            'first_name': first_name
        }}
        self.content_type = 'text'
        self.text = msg_text


def test_db_connection():
    try:
        db.session.execute('select 1')
    except exc.DatabaseError:
        assert False, 'Database error'


def test_get_users():
    dl = DBLoader('DBLoader')
    dl.get_users_fom_db()
    assert type(Loader.users) == dict, 'Wrong return type'
    assert len(Loader.users) > 0, 'Error get users from DB'


def test_add_user():
    dl = DBLoader('DBLoader')
    dl.add_user('12345678', 30, 'test_add', 'test_add')


def test_replace():
    """
    Launch MessageSender and system-monitor before testing
    """
    msg = Message('12345678', 'test_login', None, 'A')
    TBot.db_loader = DBLoader('DBLoader')
    res = TBot.replace(msg)
    assert type(res) == dict, 'Error replace data type'

