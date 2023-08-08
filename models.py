from extentions import db
from sqlalchemy.sql import func


class LibPrivileges(db.Model):
    __tablename__ = 'lib_privileges'
    __table_args__ = {
        'schema': 'TBot'
    }

    p_id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)
    name = db.Column(db.String(100))


class Users(db.Model):
    __tablename__ = 'users'
    __table_args__ = {
        'schema': 'TBot'
    }

    chat_id = db.Column(db.String(20), primary_key=True)
    login = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    privileges_id = db.Column(db.Integer, db.ForeignKey(LibPrivileges.p_id))
    date_ins = db.Column(db.DateTime(timezone=True),
                         server_default=func.now())
    description = db.Column(db.String(300))
    active = db.Column(db.Boolean, default=True)


class Poems(db.Model):
    __tablename__ = 'poems'
    __table_args__ = {
        'schema': 'TBot'
    }

    p_id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100))
    name = db.Column(db.String(200))
    text = db.Column(db.Text)


class LogRequests(db.Model):
    __tablename__ = 'log_requests'
    __table_args__ = {
        'schema': 'TBot'
    }

    lr_id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(20), db.ForeignKey(Users.chat_id))
    date_ins = db.Column(db.DateTime(timezone=True),
                         server_default=func.now())
    action = db.Column(db.String(200))
