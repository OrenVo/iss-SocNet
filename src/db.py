#!/usr/bin/python3
from src.load import load_db_config
from src.error import eprint
from flaskext.mysql import MySQL
import hashlib

class DB:
    def __init__(self, app, fname='db.ini', sect='mysql'):
        self.db = init_db(app, fname, sect)

    def cursor(self):
        return self.db.get_db().cursor()

    def check_username(self, username: str):
        cur = self.cursor()
        cur.execute(f'SELECT Login FROM Uživatel WHERE Login = \'{username}\'')
        result = cur.fetchall()
        return len(result) == 1

    def get_user(self, username: str):
        cur = self.cursor()
        cur.execute(f'SELECT * FROM Uživatel WHERE Login = \'{username}\'')
        return cur.fetchall()

    def check_password(self, password: str, username: str):
        cur = self.cursor()
        cur.execute(f'SELECT Heslo FROM Uživatel WHERE Login = \'{username}\'')
        pasw = cur.fetchall()
        p_s = pasw.split('$')
        hash_alg = hashlib.sha256(p_s[1] + password)
        return p_s[0] == hash_alg.hexdigest()

    def insert_new_user(self, username, password):
        ...

def init_db(app, fname='db.ini', sect='mysql'):
    db_config = load_db_config(fname, sect)
    app.config['MYSQL_DATABASE_HOST'] = db_config['mysql_database_host']
    app.config['MYSQL_DATABASE_PASSWORD'] = db_config['mysql_database_password']
    app.config['MYSQL_DATABASE_DB'] = db_config['mysql_database_db']
    app.config['MYSQL_DATABASE_PORT'] = int(db_config['mysql_database_port'])
    app.config['MYSQL_DATABASE_USER'] = db_config['mysql_database_user']
    mysql = MySQL()
    mysql.init_app(app)
    mysql.connect()
    eprint('Connected to database!')  # Delete
    return mysql
