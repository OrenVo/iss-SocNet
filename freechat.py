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

from src.db import DB
from src.error import eprint
from flask import Flask, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user  # TODO NEED EVERYTHING?
from flaskext.mysql import MySQL

# TO BE REMOVED
# TRANSFORM links and other input into save strings to prevent crashes
import src.load

# App initialization #
app = Flask(__name__)
app.config['SECRET_KEY'] = 'f4abb8b8384bcf305ecdf1c61156cee1'
db = DB(app)
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
        return render_template("lost_page.html")
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['psw']
        repeat = request.form['psw-repeat']

        if db.check_username(login):
            # TODO add message what was wrong
            return render_template("registration_page.html")
        if password != repeat:
            # TODO add message what was wrong & keep the username
            return render_template("registration_page.html")

        insert_new_user(username, password)
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
    # TODO NOW Dano's file (nechapem otazke)
    # TODO NOW https://stackoverflow.com/questions/50143672/passing-a-variable-from-jinja2-template-to-route-in-flask
    username = current_user.username
    # TODO get rights
    # TODO get profile_pic
    return render_template("home_page.html", username=username, rights="user", img_src=profile_pic)


@app.route("/profile/<name>/")
@app.route("/user/<name>/")
@app.route("/users/<name>/")
@app.route("/profiles/<name>/")
def profile(name):
    return render_template("welcome_page.html")
    # TODO get private
    private = False
    if private and current_user.is_anonymous:
        return render_template("tresspassing_page.html")
    return render_template("profile_page.html", username=name)


@app.route("/group/<name>/")
@app.route("/groups/<name>/")
def group(name):
    # TODO get private
    private = False
    if private and current_user.is_anonymous:
        return render_template("tresspassing_page.html")
    return render_template("group_page.html", groupname=name)


@app.route("/group/<name>/<thread>")
@app.route("/groups/<name>/<thread>")
def thread(name, thread):
    # TODO get private
    private = False
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

@app.route("/login", methods=['POST'])
def login():
    login = request.form["uname"]
    password = request.form["psw"]

    if not db.check_username(login) or not check_password(password, login):
        # TODO add message that login was unsuccesful
        return redirect(url_for("welcome"))

    return redirect(url_for("home"))


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
'''


################################################################################
# Supporting functions
################################################################################

'''
@app.before_request
def enforce_https():
    if request.headers.get('X-Forwarded-Proto') == 'http':
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)
'''


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


'''
@login_manager.unauthorized_handler
def unauthorized():
    # do stuff
    return a_response
'''


if __name__ == "__main__":
    app.run(debug=True)
