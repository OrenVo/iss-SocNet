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


from src.db import DB, init_db
from src.db import User, Group, Thread, Messages, Moderate, Is_member, Applications, Ranking
from src.error import eprint
from collections import namedtuple
from datetime import timedelta
from flask import Flask, redirect, render_template, request, session, url_for, send_file, Response, jsonify
from flask_login import current_user, LoginManager, login_required, login_user, logout_user, UserMixin
import io

'''
TODO List
Profile picture
Escape links & other input to prevent crashes and hijacking

Povinne & nepovinne udaje, oznacit povinne
https://stackoverflow.com/questions/50143672/passing-a-variable-from-jinja2-template-to-route-in-flask
Dano's file
'''

# App initialization #
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a4abb8b8384bcf305ecdf1c61156cee1'
app.app_context().push() # Nutno udělat, abych mohl pracovat s databází mimo view funkce
database = init_db(app)
db = DB(database)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "welcome"


################################################################################
# Pages
################################################################################

# Visitors #

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
    if request.method == 'GET':
        return render_template("registration_page.html")
    login = request.form['login']
    password = request.form['psw']
    repeat = request.form['psw-repeat']
    if not db.check_username(login):
        return render_template("registration_page.html", form=request.form)  # TODO add message what was wrong
    if password != repeat:
        return render_template("registration_page.html", form=request.form)  # TODO add message what was wrong & keep the username
    db.insert_new_user(login, password)
    return redirect(url_for("welcome"))  # TODO add message that it was succesful


@app.route("/login/", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for("lost"))
        return redirect(url_for("welcome"))
    login = request.form["uname"]
    password = request.form["psw"]
    if not db.check_password(password, login):
        return redirect(url_for("welcome"))  # TODO add message that login was unsuccesful & keep username
    user = User.query.filter_by(Login=login).first()
    if user:
        login_user(user)
    else:
        return redirect(url_for("welcome"))
    return redirect(url_for("home"))


@app.route("/browse/")
def guest():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    else:
        return render_template("guest_page.html")


# Users #

########  Test pro nahrávání fotek  ########
@app.route("/test")
def test():
    return render_template("test.html")

# It works, needed to push app context
@app.route("/receive_image", methods=['POST'])  # just example of uploading image
@login_required
def receive_image():
    file = request.files['img']  # change img to id in template that upload profile images
    if file:
        blob = file.read()
        mimetype = file.mimetype
        eprint(current_user.Login, mimetype, blob, sep="\n")
        db.db = database
        if db.insert_image(current_user.Login, blob, mimetype) is None:
            status_code = Response(status=404)
        else: status_code = Response(status=200)
    else:
        status_code = Response(status=404)
    return status_code

########  Konec testu nahrávání fotek  ########


@app.route("/home/")
@login_required
def home():
    username = current_user.Login
    admin = current_user.Mode & 2
    rights = "Admin" if admin else "User"
    picture = "TODO"  # TODO get profile_pic
    return render_template("home_page.html", username=username, rights="user", img_src=picture)


@app.route("/<name>/profile_image")        # Sends current_user profile image to this path
def user_img(name):
    user = User.query.filter_by(Login=name).first()
    if user is None:
        return redirect(url_for("lost"))
    private = user.Mode & 1
    if private and current_user.is_anonymous:
        return redirect(url_for("welcome"))
    file_object = io.BytesIO(user.Image)  # create file in memory
    return send_file(file_object, mimetype=user.Mimetype)  # sends file to path


@app.route("/profile_image")        # Sends current_user profile image to this path
@login_required
def profile_img():
    image = current_user.Image  # Load blob
    file_object = io.BytesIO(image)  # create file in memory
    return send_file(file_object, mimetype='image/PNG')  # sends file to path


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("welcome"))


@app.route("/profile/<name>/")
@app.route("/user/<name>/")
@app.route("/users/<name>/")
@app.route("/profiles/<name>/")
def profile(name):
    user = User.query.filter_by(Login=name).first()
    if user is None:
        return redirect(url_for("lost"))
    private = user.Mode & 1
    if private and current_user.is_anonymous:
        return redirect(url_for("welcome"))
    return render_template("profile_page.html", username=name)


@app.route("/settings/")
@login_required
def profile_settings():
    return current_user.Login + " settings page."  # TODO return settings


@app.route("/profile/<name>/settings/")
@app.route("/user/<name>/settings/")
@app.route("/users/<name>/settings/")
@app.route("/profiles/<name>/settings/")
@login_required
def admin_profile_settings(name):
    admin = current_user.Mode & 2
    owner = current_user.Login == name
    if admin:
        return name + " settings page."
    if not owner:
        return render_template("tresspassing_page.html")
    return redirect(url_for("profile_settings"))


# Groups #

@app.route("/create/group/new/")
@app.route("/create/groups/new/")
@login_required
def create_group():
    # TODO
    pass


@app.route("/create/group/<group>/newthread/")
@app.route("/create/groups/<group>/newthread/")
@login_required
def create_thread(group):
    # TODO
    pass


@app.route("/group/<group>/<thread>/new/")
@app.route("/groups/<group>/<thread>/new/")
@login_required
def send_message(group, thread):
    # TODO
    pass


@app.route("/group/<group>/<thread>/<message>/inc/")
@app.route("/groups/<group>/<thread>/<message>/inc/")
@login_required
def increment(group, thread, message):
    # TODO
    pass


@app.route("/group/<group>/<thread>/<message>/dec/")
@app.route("/groups/<group>/<thread>/<message>/dec/")
@login_required
def decrement(group, thread, message):
    # TODO
    pass


@app.route("/group/<name>/")
@app.route("/groups/<name>/")
def group(name):
    group = Group.query.filter_by(Name=name).first()
    if group is None:
        return redirect(url_for("lost"))
    private = group.Mode & 1
    if private and current_user.is_anonymous:
        return redirect(url_for("welcome"))
    return render_template("group_page.html", groupname=name)


@app.route("/group/<group>/<thread>/")
@app.route("/groups/<group>/<thread>/")
def see_posts(group, thread):
    group = Group.query.filter_by(Name=group).first()
    if group is None:
        return redirect(url_for("lost"))
    private = group.Mode & 1
    if private and current_user.is_anonymous:
        return redirect(url_for("welcome"))
    return render_template("thread_page.html", groupname=group, threadname=thread)


@app.route("/settings/group/<name>/")
@app.route("/settings/groups/<name>/")
@login_required
def group_settings(name):
    group = Group.query.filter_by(Name=name).first()
    if group is None:
        return redirect(url_for("lost"))
    admin = current_user.Mode & 2
    owner = current_user.ID == group.User_ID
    if not admin and not owner:
        return render_template("tresspassing_page.html")
    return name + " settings page."  # TODO return settings


@app.route("/notifications/group/<name>/")
@app.route("/notifications/groups/<name>/")
@login_required
def group_notifications(name):
    group = Group.query.filter_by(Name=name).first()
    if group is None:
        return redirect(url_for("lost"))
    admin = current_user.Mode & 2
    owner = current_user.ID == group.User_ID
    moderator = True  # TODO moderator
    if not admin and not owner and not moderator:
        return render_template("tresspassing_page.html")
    return name + " notifications page."  # TODO return notifications


@app.route("/apply/member/group/<name>/")
@app.route("/apply/member/groups/<name>/")
@login_required
def ask_mem(name):
    # TODO
    pass


@app.route("/apply/moderator/group/<name>/")
@app.route("/apply/moderator/groups/<name>/")
@login_required
def ask_mod(name):
    # TODO if not member: tresspass
    # TODO
    pass


# Moderation #

@app.route("/group/<group>/<thread>/<message>/delete/")
@app.route("/groups/<group>/<thread>/<message>/delete/")
@login_required
def delete(group, thread, message):
    group_instance = Group.query.filter_by(Name=group).first()
    if group_instance is None:
        return redirect(url_for("lost"))
    # TODO
    pass


@app.route("/kick/group/<group>/<name>/")
@app.route("/kick/groups/<group>/<name>/")
@login_required
def kick(group, name):
    group_instance = Group.query.filter_by(Name=name).first()
    if group_instance is None:
        return redirect(url_for("lost"))
    admin = current_user.Mode & 2
    owner = current_user.ID == group_instance.User_ID
    moderator = True  # TODO moderator
    if not admin and not owner and not moderator:
        return render_template("tresspassing_page.html")
    # Kick user
    pass


@app.route("/profile/<name>/remove/")
@app.route("/user/<name>/remove/")
@app.route("/users/<name>/remove/")
@app.route("/profiles/<name>/remove/")
@login_required
def remove(name):
    admin = current_user.Mode & 2
    owner = current_user.Login == name
    if not admin and not owner:
        return render_template("tresspassing_page.html")
    if owner:
        logout_user()
    # TODO remove user from database
    if owner:
        return redirect(url_for("welcome"))
    pass


@app.route("/profile/<name>/ban/")
@app.route("/user/<name>/ban/")
@app.route("/users/<name>/ban/")
@app.route("/profiles/<name>/ban/")
@login_required
def ban(name):
    admin = current_user.Mode & 2
    if not admin:
        return render_template("tresspassing_page.html")
    # TODO Ban user
    pass

# Other #

# TODO WE don't know if it works
@app.route('/search', methods=['GET'])
def search():
    return render_template('search.html')


# TODO WE don't know if it works
@app.route('/search_result')
def search_for():
    query = request.args.get('search')
    result = namedtuple('result', ['val', 'btn'])
    vals = [("Article1", 60), ("Article2", 50), ("Article 3", 40)]
    # below is a very simple search algorithm to filter vals based on user input:
    html = render_template('results.html', results=[result(a, b) for a, b in vals if query.lower() in a.lower()])
    return jsonify({'results': html})


@app.route("/egg/")
@app.route("/easter/")
@app.route("/easteregg/")
@app.route("/easter_egg/")
def egg():
    return render_template("egg_page.html")


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def lostdef(path):
    return render_template("lost_page.html")


@app.route("/lost")
def lost():
    return render_template("lost_page.html")


################################################################################
# Supporting functions
################################################################################

@app.before_request
def enforce_https():
    if request.headers.get('X-Forwarded-Proto') == 'http':
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=1)
    session.modified = True


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == "__main__":
    app.run(debug=True)
