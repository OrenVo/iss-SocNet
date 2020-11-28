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

from src.db import DB, init_db  # Database
from src.db import Applications, Group, Is_member, Messages, Moderate, Ranking, Thread, User  # Database objects
from src.error import eprint
from collections import namedtuple  # TODO necessary?
from datetime import timedelta
from flask import flash, Flask, jsonify, redirect, render_template, request, Response, send_file, send_from_directory, session, url_for
from flask_login import current_user, login_required, login_user, logout_user, LoginManager, UserMixin
import io
import re

"""
TODO List:
All TODOs in the file
https://stackoverflow.com/questions/50143672/passing-a-variable-from-jinja2-template-to-route-in-flask
Login redirect from welcome
Input link escaping?
"""

# App initialization #
app = Flask(__name__, static_folder='static')
app.config["SECRET_KEY"] = "a4abb8b8384bcf305ecdf1c61156cee1"
app.app_context().push()  # Nutno udělat, abych mohl pracovat s databází mimo view funkce
database = init_db(app)
db = DB(database)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "welcome"
login_manager.login_message = "You will need to log in to gain access this page."

default_group = Group.query.filter_by(ID=1).first()
default_pictures_path = '/static/pictures/defaults/'
default_profile_picture = "default_profile_picture.png"
default_group_picture = "default_group_picture.jpg"


################################################################################
# Visitors
################################################################################

# TODO Remove
@app.route("/aaaa/")
@app.route("/test/")
def test():
    return render_template("test.html")


@app.route("/")
@app.route("/index/")
@app.route("/main/")
@app.route("/welcome/")
def welcome():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return render_template("main_page.html")


@app.route("/registration/", methods=["GET", "POST"])
@app.route("/signup/", methods=["GET", "POST"])
@app.route("/sign_up/", methods=["GET", "POST"])
@app.route("/register/", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("lost"))
    if request.method == "GET":
        return render_template("registration_page.html", form=request.form)

    login = request.form["login"]
    password = request.form["psw"]
    repeat = request.form["psw-repeat"]
    if not login.isascii():
        # " " TODO
        flash("Invalid username. Please use only lower & upper case, numbers & symbols.")
        return render_template("registration_page.html", form=request.form)
    if not db.check_username(login):
        flash("Username is already taken.")
        return render_template("registration_page.html", form=request.form)
    if password != repeat:
        flash("Passwords do not match.")
        return render_template("registration_page.html", form=request.form)

    db.insert_new_user(login, password)
    flash("Your registration was succesful. You can now login.")
    return redirect(url_for("welcome"))


@app.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("lost"))
    if request.method == "GET":
        return redirect(url_for("welcome"))

    login = request.form["uname"]
    password = request.form["psw"]
    if not db.check_password(password, login):
        flash("Your credentials were incorrect. Please try again.")
        return redirect(url_for("welcome", form=request.form))

    user = User.query.filter_by(Login=login).first()
    if not user:
        flash("Something went wrong. Please try again.")
        return redirect(url_for("welcome", form=request.form))

    login_user(user)
    return redirect(url_for("home"))


@app.route("/guest/")
@app.route("/visitor/")
@app.route("/visit/")
@app.route("/browse/")
def guest():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    else:
        return redirect(url_for("group", name=default_group.Name))


################################################################################
# Users
################################################################################

@app.route("/home/")
@login_required
def home():
    name = Group.query.filter_by(ID=current_user.Last_group).first().Name
    return redirect(url_for("group", name=Group.query.filter_by(ID=current_user.Last_group).first().Name))


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
        return redirect(url_for("welcome", next=request.url))

    if current_user.is_authenticated:
        admin = current_user.Mode & 2
        owner = current_user.Login == user.Login
    else:
        admin = False
        owner = False
    # TODO member = get_membership(current_user)

    if user.Image is None:
        picture = default_pictures_path + default_profile_picture
    else:
        picture = "/profiles/" + user.Login + "/profile_image"

    member = None
    return render_template("profile_page.html", username=user.Login, name=user.Name, surname=user.Surname, description=user.Description, img_src=picture, admin=admin, owner=owner, groups=member)


@app.route("/profile_image/")
@login_required
def profile_img():
    return redirect(url_for("user_img", name=current_user.Login))


@app.route("/profile/<name>/profile_image/")
@app.route("/user/<name>/profile_image/")
@app.route("/users/<name>/profile_image/")
@app.route("/profiles/<name>/profile_image/")
def user_img(name):
    user = User.query.filter_by(Login=name).first()
    '''
    if user is None:
        return redirect(url_for("lost"))  # TODO TOP V této funkci nesmíme redirectnout.
    private = user.Mode & 1
    if private and current_user.is_anonymous:
        return redirect(url_for("welcome", next=request.url))  # TODO TOP Redirect
    '''

    if user.Image is None:
        eprint("HEEEERE: " + default_pictures_path + default_profile_picture)
        return send_from_directory(default_pictures_path, default_profile_picture, mimetype="image/png")
        # return send_file(default_pictures_path + default_profile_picture, mimetype="image/png")
    else:
        file_object = io.BytesIO(user.Image)  # Creates file in memory
        return send_file(file_object, mimetype=user.Mimetype)  # Sends file to path


@app.route("/settings/")
@login_required
def profile_settings():
    return redirect(url_for("user_settings", name=current_user.Login))


@app.route("/profile/<name>/settings/")
@app.route("/user/<name>/settings/")
@app.route("/users/<name>/settings/")
@app.route("/profiles/<name>/settings/")
@login_required
def user_settings(name):
    admin = current_user.Mode & 2
    owner = current_user.Login == name
    if not admin and not owner:
        return redirect(url_for("tresspass"))
    # TODO return settings_page.html
    return name + " settings page."


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("welcome"))


################################################################################
# Groups
################################################################################

# TODO TOP
@app.route("/image/group/<name>/")
@app.route("/image/groups/<name>/")
def group_img(name):
    group = Group.query.filter_by(Name=name).first()
    if group.Image:
        file_object = io.BytesIO(group.Image)
        return send_file(file_object, mimetype=group.Mimetype)
    else:
        return send_from_directory(default_pictures_path, default_group_picture, mimetype='image/jpg')


@app.route("/group/<name>/")
@app.route("/groups/<name>/")
def group(name):
    group = Group.query.filter_by(Name=name).first()
    if group is None:
        return redirect(url_for("lost"))
    private = group.Mode & 1
    closed = group.Mode & 2
    if closed:
        private = True
    if private and current_user.is_anonymous:
        return redirect(url_for("welcome", next=request.url))


    username = "Visitor"
    profile_pic = default_pictures_path + default_profile_picture
    if current_user.is_authenticated:
        username = current_user.Login
        if current_user.Image is not None:
            profile_pic = "/profiles/" + current_user.Login + "/profile_image"
    rights = db.getuserrights(current_user, group)
    # TODO member = get_membership(current_user)
    member = None

    group_pic = "/image/groups/" + group.Name
    group_owner = User.query.filter_by(ID=group.User_ID).first()
    if group_owner is None:
        return redirect(url_for("lost"))
    if closed and (rights["user"] or rights["visitor"]):
        threads = None
    else:
        # TODO threads = get_threads(group)
        threads = None
    return render_template("group_page.html", username=username, img_src=profile_pic, **rights, groups=member, groupname=group.Name.replace("_", " "), groupdescription=group.Description, group_src=group_pic, groupowner=group_owner.Login, private=private, closed=closed, threads=threads)


@app.route("/settings/group/<group>/")
@app.route("/settings/groups/<group>/")
@login_required
def group_settings(group):
    group = Group.query.filter_by(Name=name).first()
    if group is None:
        return redirect(url_for("lost"))

    admin = current_user.Mode & 2
    owner = current_user.ID == group.User_ID
    if not admin and not owner:
        return redirect(url_for("tresspass"))
    # TODO return group_settings.html
    return name + " settings page."


@app.route("/notifications/group/<group>/")
@app.route("/notifications/groups/<group>/")
@login_required
def group_notifications(group):
    group = Group.query.filter_by(Name=name).first()
    if group is None:
        return redirect(url_for("lost"))

    admin = current_user.Mode & 2
    owner = current_user.ID == group.User_ID
    moderator = Moderate.query.filter_by(User=current_user.ID, Group=group.ID).first()
    if not admin and not owner and not moderator:
        return redirect(url_for("tresspass"))
    # TODO return group_settings.html
    return name + " notifications page."


@app.route("/apply/member/group/<group>/")
@app.route("/apply/member/groups/<group>/")
@login_required
def ask_mem(group):
    # TODO
    pass


@app.route("/apply/moderator/group/<group>/")
@app.route("/apply/moderator/groups/<group>/")
@login_required
def ask_mod(group):
    # TODO if not member: tresspass
    # TODO
    pass


@app.route("/group/<group>/<thread>/")
@app.route("/groups/<group>/<thread>/")
def thread(group, thread):
    group = Group.query.filter_by(Name=group).first()
    if group is None:
        return redirect(url_for("lost"))
    thread = Thread.query.filter_by(Group_ID=group.ID, Name=thread).first()
    if thread is None:
        return redirect(url_for("lost"))
    private = group.Mode & 1
    if private and current_user.is_anonymous:
        return redirect(url_for("welcome", next=request.url))
    # TODO co potrebuje threadpage
    return render_template("thread_page.html", groupname=group.replace("_", " "), threadname=thread)


################################################################################
# Create
################################################################################

@app.route("/create/group/new/", methods=["GET", "POST"])
@app.route("/create/groups/new/", methods=["GET", "POST"])
@login_required
def create_group():
    # Get ma dostane na tvoriacu stranku
    # Názov
    # Práva na čítanie
    # Popis (optional)
    # Ikona (Optional)
    # Owner (current_user)
    # TODO
    Name = replace_whitespace(Name)
    pass


@app.route("/create/<group>/thread/new/", methods=["GET", "POST"])
@app.route("/create/<group>/threads/new/", methods=["GET", "POST"])
@login_required
def create_thread(group):
    # Get ma dostane na tvoriacu stranku
    # Názov
    # Popis (optional)
    # TODO
    flash("Invalid username. Please use only lower & upper case, numbers.")
    Name = replace_whitespace(Name)
    pass


@app.route("/group/<group>/<thread>/new/", methods=["POST"])
@app.route("/groups/<group>/<thread>/new/", methods=["POST"])
@login_required
def send_message(group, thread):
    # Obsah
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


################################################################################
# Moderation
################################################################################

@app.route("/group/<group>/<thread>/<message>/delete/")
@app.route("/groups/<group>/<thread>/<message>/delete/")
@login_required
def delete(group, thread, message):
    # TODO
    pass


@app.route("/kick/group/<group>/<name>/")
@app.route("/kick/groups/<group>/<name>/")
@login_required
def kick(group, name):
    # TODO
    pass


@app.route("/profile/<name>/ban/")
@app.route("/user/<name>/ban/")
@app.route("/users/<name>/ban/")
@app.route("/profiles/<name>/ban/")
@login_required
def ban(name):
    # TODO
    pass


@app.route("/profile/<name>/delete/")
@app.route("/user/<name>/delete/")
@app.route("/users/<name>/delete/")
@app.route("/profiles/<name>/delete/")
@login_required
def delete_account(name):
    # TODO
    pass


################################################################################
# Other
################################################################################

# TODO WE don"t know if it works
@app.route("/search/", methods=["GET"])
def search():
    return render_template("search.html")


# TODO WE don"t know if it works
@app.route("/search_result/")
def search_for():
    query = request.args.get("search")
    result = namedtuple("result", ["val", "btn"])
    vals = [("Article1", 60), ("Article2", 50), ("Article 3", 40)]
    # below is a very simple search algorithm to filter vals based on user input:
    html = render_template("results.html", results=[result(a, b) for a, b in vals if query.lower() in a.lower()])
    return jsonify({"results": html})


@app.route("/egg/")
@app.route("/easter/")
@app.route("/easteregg/")
@app.route("/easter_egg/")
def egg():
    return render_template("egg_page.html")


@app.route("/tresspass/")
def tresspass():
    return render_template("tresspassing_page.html")


@app.route("/lost/")
def lost():
    return render_template("lost_page.html")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def default_lost(path):
    return render_template("lost_page.html")


################################################################################
# Supporting functions
################################################################################

@app.before_request
def enforce_https():
    if request.headers.get("X-Forwarded-Proto") == "http":
        url = request.url.replace("http://", "https://", 1)
        code = 301
        return redirect(url, code=code)


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=1)
    session.modified = True  # TODO test, mam pocit že nefunguje


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/receive_image", methods=["POST"])
@login_required
def receive_image():
    file = request.files["img"]  # Change img to id in template that upload profile images
    if file:
        blob = file.read()
        mimetype = file.mimetype
        eprint(current_user.Login, mimetype, blob, sep="\n")  # TODO remove
        db.db = database
        if db.insert_image(current_user.Login, blob, mimetype) is None:
            status_code = Response(status=404)
        else:
            status_code = Response(status=200)
    else:
        status_code = Response(status=404)
    return status_code


def replace_whitespace(input):
    output = re.sub(r'\s', "_", input)
    return output


if __name__ == "__main__":
    app.run(debug=True)







@app.route("/delete/<name>/")
def delete_profile(name):
    pass


@app.route("/join/<group>/")
def join_group(group):
    pass

@app.route("/leave/<group>/")
def leave_group(group):
    pass

@app.route("/members/<group>/")
def members(group):
    pass
