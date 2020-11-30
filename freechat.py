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
import json
import re
import sys

# App initialization #
app = Flask(__name__)
app.config["SECRET_KEY"] = "a4abb8b8384bcf305ecdf1c61156cee1"
app.app_context().push()  # Nutno udělat, abych mohl pracovat s databází mimo view funkce
database = init_db(app)
db = DB(database)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "welcome"
login_manager.login_message = "You will need to log in to gain access to this page."

# Default values #
default_group_ID        = 1
default_pictures_path   = "/static/pictures/defaults/"
default_profile_picture = "default_profile_picture.png"
default_group_picture   = "default_group_picture.png"


################################################################################
# Visitors
################################################################################
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

    # Required values
    login    = request.form.get("login", None)
    password = request.form.get("psw", None)
    repeat   = request.form.get("psw-repeat", None)

    # Required values check
    if len(login) > 30 or not re.search(r"^\w+$", login):
        flash("Invalid username. Please use only English letters & numbers. Maximum is 30 characters.")
        return render_template("registration_page.html", form=request.form)
    if not db.check_username(login):
        flash("Username is already taken.")
        return render_template("registration_page.html", form=request.form)
    if password != repeat:
        flash("Passwords do not match.")
        return render_template("registration_page.html", form=request.form)

    '''
    # Optional values
    name        = request.form.get("name", None)
    surname     = request.form.get("surname", None)
    description = request.form.get("description", None)
    image       = request.files["profile_image"]
    visibility  = int(request.form.get("visibility", 0))

    # Optional values check
    if name and len(name) > 20:
        flash("Your name is too long. Maximum is 20 characters.")
        return render_template("registration_page.html", form=request.form)
    if surname and len(surname) > 20:
        flash("Your surname is too long. Maximum is 20 characters.")
        return render_template("registration_page.html", form=request.form)
    if description and len(description) > 2000:
        flash("Your description is too long. Maximum is 2000 characters.")
        return render_template("registration_page.html", form=request.form)
    if image:
        blob = image.read()
        if sys.getsizeof(blob) > (2 * 1024 * 1024):
            flash("Your image is too big. Maximum allowed size is 2MB.")
            return render_template("registration_page.html", form=request.form)
        mimetype = image.mimetype
        image = (blob, mimetype)

    db.insert_to_users(login=login, password=password, name=name, surname=surname, description=description, image=image, mode=visibility)
    '''

    db.insert_to_users(login=login, password=password)
    flash("Your registration was succesful. You can now login.")
    return redirect(url_for("welcome"))


@app.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("lost"))
    if request.method == "GET":
        return redirect(url_for("welcome"))

    login    = request.form.get("uname", None)
    password = request.form.get("psw", None)

    if not db.check_password(password, login):
        flash("Your credentials were incorrect. Please try again.")
        return render_template("main_page.html", form=request.form)

    user = User.query.filter_by(Login=login).first()
    if not user:
        flash("Something went wrong. Please try again.")
        return render_template("main_page.html", form=request.form)

    login_user(user)
    return redirect(url_for("home"))


@app.route("/guest/")
@app.route("/visitor/")
@app.route("/visit/")
@app.route("/browse/")
def guest():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return redirect(url_for("group", group_id=default_group_ID))


################################################################################
# Users
################################################################################
@app.route("/home/")
@login_required
def home():
    return redirect(url_for("group", group_id=current_user.Last_group))


@app.route("/profile/<user_id>/")
@app.route("/user/<user_id>/")
@app.route("/users/<user_id>/")
@app.route("/profiles/<user_id>/")
def profile(user_id):
    user = User.query.filter_by(ID=user_id).first()
    if user is None:
        return redirect(url_for("lost"))
    private = user.Mode & 1
    if private and current_user.is_anonymous:
        return redirect(url_for("welcome", next=request.url))

    if current_user.is_authenticated:
        admin = current_user.Mode & 2
        owner = current_user.ID == user.ID
    else:
        admin = False
        owner = False

    if user.Image is not None:
        image = "/profile_picture/" + str(user.ID)
    else:
        image = default_pictures_path + default_profile_picture

    member = db.get_membership(user)

    form = request.args.get('form')
    if form:
        form = json.loads(form)
    return render_template("profile_page.html", user_id=user.ID, username=user.Login, name=user.Name, surname=user.Surname, description=user.Description,
                           img_src=image, visibility=private, admin=admin, owner=owner, **member, form=form)


@app.route("/profile_picture/")
@login_required
def profile_img():
    return redirect(url_for("user_img", user_id=current_user.ID))


@app.route("/profile_picture/<user_id>/")
def user_img(user_id):
    user = User.query.filter_by(ID=user_id).first()
    if user is None:
        return redirect(url_for("lost"))
    private = user.Mode & 1
    if private and current_user.is_anonymous:
        return redirect(url_for("welcome", next=request.url))

    if user.Image is None:
        return redirect(url_for("lost"))
    return send_file(io.BytesIO(user.Image), mimetype=user.Mimetype)  # Creates file in memory, then sends file to path


@app.route("/profile_settings/<user_id>/", methods=["POST"])
@login_required
def user_settings(user_id):
    user = User.query.filter_by(ID=user_id).first()
    if user is None:
        return redirect(url_for("lost"))

    admin = current_user.Mode & 2
    owner = current_user.ID == user.ID
    if not admin and not owner:
        return redirect(url_for("tresspass"))

    # Current password
    current_password = request.form.get("current_password", None)
    if not admin and not db.check_password(current_password, user.Login):
        flash("Your password was incorrect. Changes were not applied.")
        return redirect(url_for("profile", user_id=user.ID, form=json.dumps(request.form)))

    # Changed values
    login       = request.form.get("login", None)
    password    = request.form.get("password1", None)
    repeat      = request.form.get("password2", None)
    name        = request.form.get("fname", None)
    surname     = request.form.get("lname", None)
    description = request.form.get("description", None)
    image       = request.files["profile_image"]
    visibility  = int(request.form.get("visibility", None))

    # Values check
    if login and (len(login) > 30 or not re.search(r"^\w+$", login)):
        flash("Invalid username. Please use only English letters & numbers. Maximum is 30 characters.")
        return redirect(url_for("profile", user_id=user.ID, form=json.dumps(request.form)))
    if login and not db.check_username(login):
        flash("Username is already taken.")
        return redirect(url_for("profile", user_id=user.ID, form=json.dumps(request.form)))
    if password and password != repeat:
        flash("Passwords do not match.")
        return redirect(url_for("profile", user_id=user.ID, form=json.dumps(request.form)))
    if name and len(name) > 20:
        flash("Your name is too long. Maximum is 20 characters.")
        return redirect(url_for("profile", user_id=user.ID, form=json.dumps(request.form)))
    if surname and len(surname) > 20:
        flash("Your surname is too long. Maximum is 20 characters.")
        return redirect(url_for("profile", user_id=user.ID, form=json.dumps(request.form)))
    if description and len(description) > 2000:
        flash("Your description is too long. Maximum is 2000 characters.")
        return redirect(url_for("profile", user_id=user.ID, form=json.dumps(request.form)))
    if image:
        blob = image.read()
        if sys.getsizeof(blob) > (2 * 1024 * 1024):
            flash("Your image is too big. Maximum allowed size is 2MB.")
            return redirect(url_for("profile", user_id=user.ID, form=json.dumps(request.form)))
        mimetype = image.mimetype
        image = (blob, mimetype)

    db.insert_to_users(id=user.ID, login=login, password=password, name=name, surname=surname, description=description, image=image, mode=visibility)
    flash("Your changes were applied.")
    return redirect(url_for("profile", user_id=user.ID))


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("welcome"))


@app.route("/delete/profile/<user_id>/")
@app.route("/delete/user/<user_id>/")
@app.route("/delete/users/<user_id>/")
@app.route("/delete/profiles/<user_id>/")
@login_required
def delete_account(user_id):
    user = User.query.filter_by(ID=user_id).first()
    if user is None:
        return redirect(url_for("lost"))

    admin = current_user.Mode & 2
    owner = current_user.ID == user.ID
    if not admin and not owner:
        return redirect(url_for("tresspass"))

    if admin:
        db.delete_from_db(user)
        flash("Account has been deleted.")
        return redirect(url_for("home"))
    else:
        logout_user()
        db.delete_from_db(user)
        flash("Your account has been deleted.")
        return redirect(url_for("welcome"))


################################################################################
# Groups
################################################################################
@app.route("/create/group/", methods=["POST"])
@login_required
def create_group():
    name        = request.form.get("group_name", None)
    description = request.form.get("description", None)
    image       = request.files["group_image"]
    visibility  = int(request.form.get("visibility", None))
    owner       = current_user.ID

    # Values check
    if len(name) > 30:
        flash("Group name is too long. Maximum is 30 characters.")
        return redirect(url_for("group", group_id=current_user.Last_group, form=json.dumps(request.form)))
    if not db.check_groupname(name):
        flash("Group name is already taken. Please use different name.")
        return redirect(url_for("group", group_id=current_user.Last_group, form=json.dumps(request.form)))
    if description and len(description) > 2000:
        flash("Group description is too long. Maximum is 2000 characters.")
        return redirect(url_for("group", group_id=current_user.Last_group, form=json.dumps(request.form)))
    if image:
        blob = image.read()
        if sys.getsizeof(blob) > (2 * 1024 * 1024):
            flash("Group image is too big. Maximum allowed size is 2MB.")
            return redirect(url_for("group", group_id=current_user.Last_group, form=json.dumps(request.form)))
        mimetype = image.mimetype
        image = (blob, mimetype)

    id = db.insert_to_group(name=name, description=description, image=image, mode=visibility, user_id=owner)
    return redirect(url_for("group", group_id=id))


@app.route("/group/<group_id>/")
@app.route("/groups/<group_id>/")
def group(group_id):
    group = Group.query.filter_by(ID=group_id).first()
    if group is None:
        return redirect(url_for("lost"))
    private = group.Mode & 1
    if private and current_user.is_anonymous:
        return redirect(url_for("welcome", next=request.url))

    if group.Image is not None:
        image = "/group_picture/" + str(group.ID)
    else:
        image = default_pictures_path + default_group_picture
    group_owner = User.query.filter_by(ID=group.User_ID).first()
    if group_owner is None:
        return redirect(url_for("lost"))

    if current_user.is_anonymous:
        user_id = None
        username = "Visitor"
        profile_pic = default_pictures_path + default_profile_picture
    else:
        user_id = current_user.ID
        username = current_user.Login
        if current_user.Image is not None:
            profile_pic = "/profile_picture/" + str(current_user.ID)
        else:
            profile_pic = default_pictures_path + default_profile_picture
        db.insert_to_users(id=current_user.ID, last_group_id=group.ID)

    member = db.get_membership(current_user)
    rights = db.getuserrights(current_user, group)

    closed = group.Mode & 2
    if closed and (rights["user"] or rights["visitor"]):
        threads = None
    else:
        threads = db.get_threads(group)

    form = request.args.get('form')
    if form:
        form = json.loads(form)
    return render_template("group_page.html", group_id=group.ID, groupname=group.Name, groupdescription=group.Description, group_src=image,
                           groupowner_id=group_owner.ID, group_owner=group_owner.Login, private=private, closed=closed, threads=threads, user_id=user_id,
                           username=username, img_src=profile_pic, **member, **rights, form=form)


@app.route("/group_picture/<group_id>/")
def group_img(name):
    group = Group.query.filter_by(ID=group_id).first()
    if group is None:
        return redirect(url_for("lost"))
    private = group.Mode & 1
    if private and current_user.is_anonymous:
        return redirect(url_for("welcome", next=request.url))

    if group.Image is None:
        return redirect(url_for("lost"))
    return send_file(io.BytesIO(group.Image), mimetype=group.Mimetype)  # Creates file in memory, then sends file to path


@app.route("/group_settings/<group_id>/")
@login_required
def group_settings(group_id):
    group = Group.query.filter_by(ID=group_id).first()
    if group is None:
        return redirect(url_for("lost"))

    admin = current_user.Mode & 2
    owner = current_user.ID == group.User_ID
    if not owner or not admin:
        return redirect(url_for("lost"))

    if request.method == "GET":
        return render_template("group_settings.html", group_id=group.ID, form=request.form)

    name        = request.form.get("group_name", None)
    description = request.form.get("description", None)
    image       = request.files["group_image"]
    mode        = int(request.form.get("visibility", None))

    # Values check
    if len(name) > 30:
        flash("Group name is too long. Maximum is 30 characters.")
        return render_template("group_settings.html", group_id=group.ID, form=request.form)
    if not db.check_groupname(name):
        flash("Group name is already taken. Please use different name.")
        return render_template("group_settings.html", group_id=group.ID, form=request.form)
    if description and len(description) > 2000:
        flash("Group description is too long. Maximum is 2000 characters.")
        return render_template("group_settings.html", group_id=group.ID, form=request.form)
    if image:
        blob = image.read()
        if sys.getsizeof(blob) > (2 * 1024 * 1024):
            flash("Group image is too big. Maximum allowed size is 2MB.")
            return render_template("group_settings.html", group_id=group.ID, form=request.form)
        mimetype = image.mimetype
        image = (blob, mimetype)

    id = db.insert_to_group(name=name, description=description, image=image, mode=visibility, user_id=owner)
    flash("Your changes have been applied.")
    return redirect(url_for("group", group_id=id))


@app.route("/group_notifications/<group_id>/", methods=["POST"])
@login_required
def group_notifications(group_id):
    group = Group.query.filter_by(ID=group_id).first()
    if group is None:
        return redirect(url_for("lost"))

    admin     = current_user.Mode & 2
    owner     = current_user.ID == group.User_ID
    moderator = Moderate.query.filter_by(User=current_user.ID, Group=group.ID).first()
    if not owner or not admin or not moderator:
        return redirect(url_for("tresspass"))

    notifications = db.get_applicants(group)
    return render_template("notifications.html", group_id=group.ID, notifications=notifications,
                           admin=admin, owner=owner, moderator=moderator, form=request.form)


@app.route("/group_members/<group_id>/", methods=["POST"])
def members(group_id):
    group = Group.query.filter_by(ID=group_id).first()
    if group is None:
        return redirect(url_for("lost"))
    private = group.Mode & 1
    if private and current_user.is_anonymous:
        return redirect(url_for("welcome", next=request.url))

    rights = db.getuserrights(current_user, group)
    closed = group.Mode & 2
    if closed and (rights["user"] or rights["visitor"]):
        return redirect(url_for("tresspass"))

    group_owner = User.query.filter_by(ID=group.User_ID).first()
    if group_owner is None:
        return redirect(url_for("lost"))
    moderators = db.get_moderators(group)
    members = db.get_members(group)

    return render_template("group_members.html", group_id=group.ID, group_owner=group_owner, moderators=moderators, members=members, **rights)


@app.route("/apply/member/<group_id>/")
@login_required
def ask_mem(group_id):
    group = Group.query.filter_by(ID=group_id).first()
    if group is None:
        return redirect(url_for("lost"))

    owner     = current_user.ID == group.User_ID
    moderator = Moderate.query.filter_by(User=current_user.ID, Group=group.ID).first()
    member    = Is_member.query.filter_by(User=current_user.ID, Group=group.ID).first()
    if owner or moderator or member:
        return redirect(url_for("lost"))

    db.insert_to_applications(current_user.ID, group.ID, True)
    flash("Your request has been sent for a review.")
    return redirect(url_for("home"))


@app.route("/apply/moderator/<group_id>/")
@login_required
def ask_mod(group_id):
    group = Group.query.filter_by(ID=group_id).first()
    if group is None:
        return redirect(url_for("lost"))

    member = Is_member.query.filter_by(User=current_user.ID, Group=group.ID).first()
    if not member:
        return redirect(url_for("lost"))

    db.insert_to_applications(current_user.ID, group.ID, False)
    flash("Your request has been sent for a review.")
    return redirect(url_for("home"))


@app.route("/accept/<application_id>")
@login_required
def accept_application(application_id):
    application = Applications.query.filter_by(ID=application_id).first()
    if application is None:
        return redirect(url_for("lost"))
    group = Group.query.filter_by(ID=application.Group).first()
    if group is None:
        db.delete_from_db(application)
        return redirect(url_for("home"))

    # User rights
    admin     = current_user.Mode & 2
    owner     = current_user.ID == group.User_ID or admin
    moderator = Moderate.query.filter_by(User=current_user.ID, Group=group.ID).first()

    # Moderator request
    if not owner and not application.Membership:
        return redirect(url_for("tresspass"))
    # Membership request
    if not owner or not moderator:
        return redirect(url_for("tresspass"))

    user = User.query.filter_by(ID=application.User).first()
    if user is None:
        db.delete_from_db(application)
        return redirect(url_for("group_notifications", group_id=application.Group))

    membership = Is_member.query.filter_by(User=user.ID, Group=group.ID).first()
    if application.Membership and not membership:
        db.insert_to_membership(user.ID, group.ID)
    elif not application.Membership and not Moderate.query.filter_by(User=user.ID, Group=group.ID).first():
        db.insert_to_moderate(user.ID, group.ID)
        db.delete_from_db(membership)

    db.delete_from_db(application)
    return redirect(url_for("group_notifications", group_id=application.Group))


@app.route("/reject/<application_id>")
@login_required
def reject_application(application_id):
    application = Applications.query.filter_by(ID=application_id).first()
    if application is None:
        return redirect(url_for("lost"))
    group = Group.query.filter_by(ID=application.Group).first()
    if group is None:
        db.delete_from_db(application)
        return redirect(url_for("home"))

    # User rights
    admin     = current_user.Mode & 2
    owner     = current_user.ID == group.User_ID or admin
    moderator = Moderate.query.filter_by(User=current_user.ID, Group=group.ID).first()

    # Moderator request
    if not owner and not application.Membership:
        return redirect(url_for("tresspass"))
    # Membership request
    if not owner or not moderator:
        return redirect(url_for("tresspass"))

    db.delete_from_db(application)
    return redirect(url_for("group_notifications", group_id=application.Group))


@app.route("/leave/<group_id>/")
@login_required
def leave_group(group_id):
    redirect(url_for("kick", group_id=group_id, user_id=current_user.ID))


@app.route("/delete/group/<group_id>/")
@app.route("/delete/groups/<group_id>/")
@login_required
def delete_group(group_id):
    # TODO iba owner alebo admin
    pass


################################################################################
# Threads
################################################################################
@app.route("/create/thread/<group_id>/")
def create_thread(group_id):
    # TODO
    pass


@app.route("/group/<group_id>/<thread_id>")
@app.route("/groups/<group_id>/<thread_id>")
def thread(group_id, thread_id):
    group = Group.query.filter_by(ID=group_id).first()
    if group is None:
        return redirect(url_for("lost"))
    thread = Thread.query.filter_by(Group_ID=group.ID, ID=thread_id).first()
    if thread is None:
        return redirect(url_for("lost"))
    closed = group.Mode & 2
    private = group.Mode & 1
    if private and current_user.is_anonymous:
        return redirect(url_for("welcome", next=request.url))
    rights = db.getuserrights(current_user, group)
    closed = group.Mode & 2
    if closed and (rights["user"] or rights["visitor"]):
        return redirect(url_for("tresspass"))
    profile_pic = default_pictures_path + default_profile_picture
    if current_user.is_anonymous:
        username = "Visitor"
        profile_pic = default_pictures_path + default_profile_picture
    else:
        username = current_user.Login
        if current_user.Image is None:
            profile_pic = default_pictures_path + default_profile_picture
        else:
            profile_pic = "/profiles/" + current_user.Login + "/profile_image"

    return render_template("thread_page.html", username=username, img_src=profile_pic, **rights,
                           groupname=group.Name.replace("", " "), threadname=thread.Name,
                           description=thread.Description, posts=db.get_messages(thread, 50))

@app.route("/create_message/<group_id>/<thread_id>/")
@login_required
def create_message(group_id, thread_id):
    thread = Thread.query.filter_by(ID=thread_id).first()
    db.insert_to_messages(current_user, thread, thread_id, Content=request.form['content'])

@app.route("/delete/group/<group_id>/<thread_id>/")
@app.route("/delete/groups/<group_id>/<thread_id>/")
@login_required
def delete_thread(group_id, thread_id):
    # TODO admin, owner, moderator, majtel vlakna?
    pass


################################################################################
# Other
################################################################################
@app.route("/search/", methods=["POST"])
def search():
    result = db.search_user_group(request.form.get("search", None))
    return json.dumps(result)
    return render_template("search.html", **result)  # TODO co co s vysledkami


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
    session.modified = True


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == "__main__":
    app.run(debug=True)
