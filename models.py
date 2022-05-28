from extentions import db
from sqlalchemy.sql import func


class LibPrivileges(db.Model):
    __tablename__ = 'lib_privileges'
    __table_args__ = {
        'schema': 'TBot'
    }

    p_id = db.Column(db.Integer, primary_key=True)
    valuse = db.Column(db.Integer)
    name = db.Column(db.String(100))


class Users(db.Model):
    __tablename__ = 'users'
    __table_args__ = {
        'schema': 'TBot'
    }

    chat_id = db.Column(db.String(20), primary_key=True)
    login = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    privileges_id = db.Column(db.Integer, db.ForeignKey('lib_privileges.p_id'))
    date_ins = db.Column(db.DateTime(timezone=True),
                         server_default=func.now())