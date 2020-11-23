#!/usr/bin/python3
from src.load import load_db_config
from src.error import eprint
from flaskext.mysql import MySQL


class DB:
    def __init__(self, app, fname='db.ini', sect='mysql'):
        self.db = init_db(app, fname, sect)

    def cursor(self):
        return self.db.get_db().cursor()

    def check_username(self, username):
        cur = self.cursor()
        cur.execute(f'SELECT Login FROM Uživatel WHERE Login = \'{username}\'')
        result = cur.fetchall()
        return len(result) == 1


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