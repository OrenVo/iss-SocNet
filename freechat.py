#!/usr/bin/env python3
# -*- coding: utf-8 -*-

################################################################################
# @project Free Chat - IIS2020(Sociální síť: diskuse v diskusních skupinách)
#
# @file freechat.py
# @brief Online message forum
#
# @author Roman Fulla <xfulla00>
# @author Vojtech Ulej <xulejv00>
################################################################################


from src.db import DB, init_db, User
from src.error import eprint
from collections import namedtuple
from datetime import timedelta
from flask import Flask, redirect, render_template, request, url_for, session
from flask_login import current_user, LoginManager, login_required, login_user, logout_user, UserMixin

'''
TODO List
Profile picture
Dano's file
https://stackoverflow.com/questions/50143672/passing-a-variable-from-jinja2-template-to-route-in-flask
Escape links & other input to prevent crashes and hijacking
'''

# App initialization #
app = Flask(__name__)
app.config['SECRET_KEY'] = 'f4abb8b8384bcf305ecdf1c61156cee1'
database = init_db(app)
db = DB(database)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "welcome"


################################################################################
# Pages
################################################################################

# Visitor pages #

@app.route("/")
@app.route('/index/')
@app.route('/main/')
@app.route('/welcome/')
def welcome():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return render_template("main_page.html")


@app.route("/registration/", methods=['GET', 'POST'])
@app.route("/signup/", methods=['GET', 'POST'])
@app.route("/sign_up/", methods=['GET', 'POST'])
@app.route("/register/", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("lost"))
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['psw']
        repeat = request.form['psw-repeat']
        if not db.check_username(login):
            # TODO add message what was wrong
            return render_template("registration_page.html")
        if password != repeat:
            # TODO add message what was wrong & keep the username
            return render_template("registration_page.html")
        db.insert_new_user(login, password)
        # TODO add message that it was succesful
        return redirect(url_for("welcome"))
    return render_template("registration_page.html")


@app.route("/browse/")
def guest():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    else:
        return render_template("guest_page.html")


# User pages #

@app.route("/home/")
@login_required
def home():
    username = current_user.Login
    mode = current_user.Mode
    admin = mode & 2
    rights = "Admin" if admin else "User"
    return rights
    picture = "TODO"  # TODO get profile_pic
    return render_template("home_page.html", username=username, rights="user", img_src=picture)


@app.route("/profile/<name>/")
@app.route("/user/<name>/")
@app.route("/users/<name>/")
@app.route("/profiles/<name>/")
def profile(name):
    user = name
    private = user.Mode & 1
    if private and current_user.is_anonymous:
        return render_template("tresspassing_page.html")
    return render_template("profile_page.html", username=name)


@app.route("/group/<name>/")
@app.route("/groups/<name>/")
def group(name):
    group = name
    private = group.Mode & 1
    if private and current_user.is_anonymous:
        return render_template("tresspassing_page.html")
    return render_template("group_page.html", groupname=name)


@app.route("/group/<name>/<thread>")
@app.route("/groups/<name>/<thread>")
def thread(name, thread):
    group = name
    private = group.Mode & 1
    if private and current_user.is_anonymous:
        return render_template("tresspassing_page.html")
    return render_template("thread_page.html", groupname=name, threadname=thread)


# Other pages #

@app.route("/egg/")
@app.route("/easter/")
@app.route("/easteregg/")
@app.route("/easter_egg/")
def egg():
    return render_template("egg_page.html")


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def lost(path):
    return render_template("lost_page.html")


################################################################################
# Requests
################################################################################

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for("lost"))
        return redirect(url_for("welcome"))
    login = request.form["uname"]
    password = request.form["psw"]
    if not db.check_password(password, login):
        # TODO add message that login was unsuccesful & keep username
        return redirect(url_for("welcome"))

    user = User.query.filter_by(Login=login).first()
    login_user(user)
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("welcome"))


'''
@app.route("/profile/<name>/settings")
@app.route("/profiles/<name>/settings")
@app.route("/user/<name>/settings")
@app.route("/users/<name>/settings")
@login_required
def profile_settings(name):
    if current_user.username != name:
        return render_template("tresspassing_page.html")
    return name + " settings page."
    # TODO return settings


@app.route("/group/<name>/settings")
@app.route("/groups/<name>/settings")
@login_required
def group_settings(name):
    if current_user.id != group.owner:
        return render_template("tresspassing_page.html")
    return name + " settings page."
    # TODO return settings

@app.route("/group/<name>/notifications")
@app.route("/groups/<name>/notifications")
@login_required
def group_settings(name):
    if current_user.id != group.owner:
        return render_template("tresspassing_page.html")
    return name + " settings page."
    # TODO return settingsň

@app.route("/group/<name>/<thread>")
@app.route("/groups/<name>/<thread>")
@login_required
def see_posts(name):
    if current_user.id != group.owner:
        return render_template("tresspassing_page.html")
    return name + " settings page."
    # TODO return settings


@app.route("/group/<name>/<thread>")
@app.route("/groups/<name>/<thread>")
@login_required
def increment(name):
    if current_user.id != group.owner:
        return render_template("tresspassing_page.html")
    return name + " settings page."
    # TODO return settings

@app.route("/group/<name>/<thread>")
@app.route("/groups/<name>/<thread>")
@login_required
def decrement(name):
    if current_user.id != group.owner:
        return render_template("tresspassing_page.html")
    return name + " settings page."
    # TODO return settings

@app.route("/group/<name>/<thread>")
@app.route("/groups/<name>/<thread>")
@login_required
def send_message(name):
    if current_user.id != group.owner:
        return render_template("tresspassing_page.html")
    return name + " settings page."
    # TODO return settings

@app.route("/group/<name>/<thread>")
@app.route("/groups/<name>/<thread>")
@login_required
def create_group(name):
    if current_user.id != group.owner:
        return render_template("tresspassing_page.html")
    return name + " settings page."
    # TODO return settings


@app.route("/group/<name>/<thread>")
@app.route("/groups/<name>/<thread>")
@login_required
def create_thread(name):
    if current_user.id != group.owner:
        return render_template("tresspassing_page.html")
    return name + " settings page."
    # TODO return settings
'''


################################################################################
# Supporting functions
################################################################################

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=1)
    session.modified = True


@app.before_request
def enforce_https():
    if request.headers.get('X-Forwarded-Proto') == 'http':
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# WE don't know if it works
@app.route('/search', methods=['GET'])
def search():
    return flask.render_template('search.html')


# WE don't know if it works
@app.route('/search_result')
def search_for():
    query = flask.request.args.get('search')
    result = namedtuple('result', ['val', 'btn'])
    vals = [("Article1", 60), ("Article2", 50), ("Article 3", 40)]
    # below is a very simple search algorithm to filter vals based on user input:
    html = flask.render_template('results.html', results=[result(a, b) for a, b in vals if query.lower() in a.lower()])
    return flask.jsonify({'results': html})


if __name__ == "__main__":
    app.run(debug=True)
