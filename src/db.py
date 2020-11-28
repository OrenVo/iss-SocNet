#!/usr/bin/python3
from sqlalchemy import func

from src.error import eprint
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import hashlib
from configparser import ConfigParser
import os.path
from sqlalchemy.orm import defer, undefer
import secrets
from sqlalchemy.ext.automap import automap_base

mysql = SQLAlchemy()
Base = automap_base(mysql.Model)


class User(Base, UserMixin):
    __tablename__ = 'users'

    def get_id(self):
        from flask._compat import text_type
        return text_type(self.ID)


class Group(Base):
    __tablename__ = 'group'


class Thread(Base):
    __tablename__ = 'thread'


class Messages(Base):
    __tablename__ = 'messages'


class Moderate(Base):
    __tablename__ = 'moderate'


class Is_member(Base):
    __tablename__ = 'is_member'


class Applications(Base):
    __tablename__ = 'applications'


class Ranking(Base):
    __tablename__ = 'ranking'


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

    def insert_image(self, login: str, blob, mimetype=None):
        user = User.query.filter_by(Login=login).first()
        if not user:
            return None
        user.Image = blob
        user.Mimetype = mimetype
        self.db.session.commit()
        return user

    def insert_new_user(self, username, password):
        psw = self.create_password(password)
        new_user = User(Login=username, Password=psw, Last_group=1)
        instance = self.db.session.query(User).filter_by(Login=username).first()
        if instance is None:
            self.db.session.add(new_user)
            self.db.session.commit()
            return new_user
        else:
            return None

    def check_password(self, password: str, username: str) -> bool:
        user = self.db.session.query(User).filter_by(Login=username).first()
        if user is None:
            return False
        p_s = user.Password.split('$')
        hash_alg = hashlib.sha256((p_s[1] + password).encode())
        return p_s[0] == hash_alg.hexdigest()

    def change_password(self, login: str, new_psw: str) -> None:
        user = self.db.session.query(User).filter_by(Login=login)
        new_hash = self.create_password(new_psw)
        user.Password = new_hash
        self.db.session.commit()

    @staticmethod
    def create_password(password: str):
        salt = secrets.token_hex(16)
        hash_alg = hashlib.sha256((salt + password).encode())
        return hash_alg.hexdigest() + "$" + salt

    def check_username(self, username: str):
        user = self.db.session.query(User).filter_by(Login=username).first()
        return user is None

    def get_user(self, username):
        instance = self.db.session.query(User).filter_by(Login=username).first()
        return instance

    def get_membership(self, user: User) -> dict:
        Ownership = self.db.session.query(Group).filter_by(User_ID=user.ID).all()
        Moderator = self.db.session.query(Moderate).filter_by(User=user.ID).all()
        Member = self.db.session.query(Is_member).filter_by(User=user.ID).all()
        for mem in Member:
            moderator = [x for x in Moderator if x.Group == mem.Group]
            if moderator:
                Member.delete(mem)
        gowner = list()
        gmoderator = list()
        gmember = list()
        for own in Ownership:
            path = f'/image/group/{own.Name}/' if own.Image else '/static/pictures/defaults/default_group_picture.jpg'
            gowner.append((own, path))
        for mod in Moderator:
            path = f'/image/group/{mod.Name}/' if mod.Image else '/static/pictures/defaults/default_group_picture.jpg'
            gmoderator.append((mod, path))
        for mem in Member:
            path = f'/image/group/{mem.Name}/' if mem.Image else '/static/pictures/defaults/default_group_picture.jpg'
            gmember.append((mem, path))
        return {'gowner': gowner, 'gmoderator': gmoderator, 'gmember': gmember}

    def get_threads(self, group: Group) -> list:
        return self.db.session.query(Thread).filter_by(Group_ID=group.ID).all()

    def send_message(self, user, group, thread_name, message):
        ...  # TODO send_message

    def insert_to_user(self, ID: int = None, login: str = None, name: str = None, surname: str = None, description: str = None, mode: int = None, image: tuple = None, password: str = None, last_group_id: int = None):
        if ID is None:   # user doesn't exist create new
            ...
        else:  # user should exist just update him
            ...
        if login:
            ...
        if name:
            ...
        if surname:
            ...
        if description:
            ...
        if mode:
            ...
        if image:
            ...
        if password:
            ...
        if last_group_id:
            ...

    def getuserrights(self, user, group) -> dict:
        result = {
            'admin': None,
            'owner': None,
            'moderator': None,
            'member': None,
            'user': None,
            'visitor': None
        }
        if user.is_authenticated:
            result['user'] = True
        else:
            result['visitor'] = True
            return result  # TODO visitor nema ine ako vstavane funkcie takze by to padlo #Roman
        # user = self.db.session.query(User).filter_by(Login=username).first()
        # group = self.db.session.query(Group).filter_by(ID=group).first()
        if user.Mode & 2:
            result['admin'] = True
        elif user.ID == group.User_ID:
            result['owner'] = True
        elif self.db.session.query(Moderate).filter_by(User=user.ID, Group=group.ID).first():
            result['moderator'] = True
        elif self.db.session.query(Is_member).filter_by(User=user.ID, Group=group.ID).first():
            result['member'] = True

        return result


# Note this function must be called before others functions that works with database!!!
def init_db(app, fname='db.ini', sect='mysql'):
    db_config = load_db_config(fname, sect)
    host = db_config['mysql_database_host']
    psw = db_config['mysql_database_password']
    db = db_config['mysql_database_db']
    port = db_config['mysql_database_port']
    user = db_config['mysql_database_user']
    app.config[
        'SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{user}:{psw}@{host}:{port}/{db}'  # Dano proof version
    # 'SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqldb://{user}:{psw}@{host}:{port}/{db}?ssl=true'  # change driver to mysqldb and add ?ssl=true for better performance and security      Original co funguje vsetkym okrem Danovho Linuxu
    app.config['SQLALCHEMY_ECHO'] = True  # TODO debugging info delete me for production
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 600
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 30
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    global mysql
    mysql.init_app(app)
    global Base
    Base.prepare(mysql.engine, reflect=True)
    # global User, Group, Thread, Messages, Moderate, Is_member, Applications, Ranking
    # User = Base.classes.users
    # Group = Base.classes.group
    # Thread = Base.classes.thread
    # Message = Base.classes.messages
    # Moderate = Base.classes.moderate
    # Is_member = Base.classes.is_member
    # Application = Base.classes.applications
    # Ranking = Base.classes.ranking
    return mysql
