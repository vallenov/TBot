import pytest
from sqlalchemy import exc

from loaders.db_loader import DBLoader
from extentions import db
from users import tbot_users, MemUsers
from TBot import TBot
from loaders.loader import LoaderResponse


class Message:
    def __init__(self, chat_id, login, first_name, msg_text):
        self.json = {'chat': {
            'id': chat_id,
            'username': login,
            'first_name': first_name
        }}
        self.content_type = 'text'
        self.text = msg_text


@pytest.fixture(scope='function')
def disable_db_commit():

    def disable_commits():
        db.session.rollback()

    _commit = db.session.commit
    db.session.commit = disable_commits
    yield
    db.session.commit = _commit


def test_db_connection():
    try:
        db.session.execute('select 1')
    except exc.DatabaseError:
        assert False, 'Database error'


def test_get_users():
    dl = DBLoader()
    dl.get_users_from_db()
    assert type(tbot_users) is MemUsers, 'Wrong return type'
    assert len(tbot_users.all()) > 0, 'Error get users from DB'


def test_add_user(disable_db_commit):
    dl = DBLoader()
    chat_id = '12345678'
    dl.add_user(chat_id=chat_id, privileges=30, first_name='test', login='')
    tbot_users.del_user(chat_id)


def test_replace(disable_db_commit):
    """
    Launch MessageSender and system-monitor before testing
    """
    msg = Message('12345678', 'test_login', None, 'A')
    TBot.db_loader = DBLoader()
    tbot = TBot()
    tbot.init_bot()
    res = tbot.replace(msg)
    assert type(res) is LoaderResponse, 'Error replace data type'
