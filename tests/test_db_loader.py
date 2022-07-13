from sqlalchemy import exc

from loaders.loader import Loader
from loaders.db_loader import DBLoader
from extentions import db


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

