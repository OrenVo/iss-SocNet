#!/usr/bin/python3
from src.error import eprint
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import hashlib
from configparser import ConfigParser
import os.path
from sqlalchemy.orm import defer, undefer
import secrets
from sqlalchemy.ext.automap import automap_base


def load_db_config(fname='db.ini', sect='mysql'):
    """Load config file with information to connect to DB
       :returns dictionary of parameters loaded from file fname section sect
    """
    if not os.path.isfile(fname):
        raise Exception(f'File: {fname} doesn\'t exist.')
    config = ConfigParser()
    config.read(fname)

    db = {}
    if config.has_section(sect):
        params = config.items(sect)
        for par in params:
            db[par[0]] = par[1]
    else:
        raise Exception(f'Cannot find {sect} section in file: {fname}')
    return db


class DB:
    def __init__(self, db):
        self.db = db

    # TODO USERNAME CASE INSENSITIVE
    def insert_new_user(self, username, password):
        psw = self.create_password(password)
        eprint("\n", psw, "\n")
        new_user = User(Login=username, Password=psw)
        instance = mysql.session.query(User).filter_by(Login=username).first()
        if instance is None:
            mysql.session.add(new_user)
            try:
                mysql.session.commit()
            except Exception as e:
                eprint(str(e))
                mysql.session.rollback()
            return new_user
        else:
            return None

    def check_password(self, password: str, username: str):
        user = self.db.session.query(User).filter_by(Login=username).first()
        if user is None: return False
        p_s = user.Password.split('$')
        hash_alg = hashlib.sha256((p_s[1] + password).encode())
        return p_s[0] == hash_alg.hexdigest()

    @staticmethod
    def create_password(password: str):
        salt = secrets.token_hex(16)
        hash_alg = hashlib.sha256((salt + password).encode())
        return hash_alg.hexdigest() + "$" + salt

    def check_username(self, username: str):
        user = self.db.session.query(User).filter_by(Login=username).first()
        return user is None

    # GOOD TO GO
    def get_user(self, username):
        instance = self.db.session.query(User).filter_by(Login=username).first()
        return instance

    # CHECK ME
    def get_id(self):
        # TODO
        pass


mysql = SQLAlchemy()
Base = automap_base(mysql.Model)


# CHECK ME
class User(Base, UserMixin, mysql.Model):
    __tablename__ = 'users'

    def get_id(self):
        from flask._compat import text_type
        return text_type(self.ID)


# Note this function must be called before others functions that works with database!!!
def init_db(app, fname='db.ini', sect='mysql'):
    db_config = load_db_config(fname, sect)
    host = db_config['mysql_database_host']
    psw = db_config['mysql_database_password']
    db = db_config['mysql_database_db']
    port = db_config['mysql_database_port']
    user = db_config['mysql_database_user']
    app.config[
        'SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{user}:{psw}@{host}:{port}/{db}'  # change driver to mysqldb and add ?ssl=true for better performance and security
    app.config['SQLALCHEMY_ECHO'] = True  # TODO debugging info delete me for production
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 600
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 30
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    global mysql
    mysql = SQLAlchemy(app)
    global Base
    Base.prepare(mysql.engine, reflect=True)
    global User, Group, Thread, Messages, Moderate, Is_member, Applications, Ranking
    # User = Base.classes.users
    Group = Base.classes.group
    Thread = Base.classes.thread
    Message = Base.classes.messages
    Moderate = Base.classes.moderate
    Is_member = Base.classes.is_member
    Application = Base.classes.applications
    Ranking = Base.classes.ranking
    # admin = User(Login='Admin', Password=DB.create_password('nimdA'))
    # instance = mysql.session.query(User).filter_by(Login='Admin').first()
    # if instance is None:
    #    mysql.session.add(admin,)
    #    mysql.session.commit()
    return mysql
