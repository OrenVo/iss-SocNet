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
    # Optional values  # TODO
    name        = request.form.get("name", None)
    surname     = request.form.get("surname", None)
    description = request.form.get("description", None)
    image       = request.form.get("profile_image", None)
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

    db.insert_to_users(login=login, password=password, visibility=0)
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
    return redirect(url_for("group", group=default_group_ID))


################################################################################
# Users
################################################################################
@app.route("/home/")
@login_required
def home():
    return redirect(url_for("group", group=current_user.Last_group))


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
        image = "/profile_picture/" + user.ID
    else:
        image = default_pictures_path + default_profile_picture

    member = db.get_membership(user)
    return render_template("profile_page.html", user_id=user.ID, username=user.Login, name=user.Name, surname=user.Surname, description=user.Description, img_src=image, visibility=private, admin=admin, owner=owner, **member)


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
    if not admin or not db.check_password(current_password, user.Login):
        flash("Your password were incorrect. Changes were not applied.")
        return redirect(url_for("profile", user_id=user.ID, form=json.dumps(request.form)))

    # Changed values
    login       = request.form.get("login", None)
    password    = request.form.get("password1", None)
    repeat      = request.form.get("password2", None)
    name        = request.form.get("fname", None)
    surname     = request.form.get("lname", None)
    description = request.form.get("description", None)
    image       = request.form.get("profile_image", None)
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


################################################################################
# Groups
################################################################################
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
        image = "/group_picture/" + group.ID
    else:
        image = default_pictures_path + default_group_picture
    group_owner = User.query.filter_by(ID=group.User_ID).first()
    if group_owner is None:
        return redirect(url_for("lost"))

    if current_user.is_anonymous:
        username = "Visitor"
        profile_pic = default_pictures_path + default_profile_picture
    else:
        username = current_user.Login
        if current_user.Image is not None:
            profile_pic = "/profile_picture/" + current_user.ID
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

    return render_template("group_page.html", username=username, img_src=profile_pic, **member, **rights, groupname=group.Name.replace("_", " "), groupdescription=group.Description, group_src=group_pic, groupowner=group_owner.Login, private=private, closed=closed, threads=threads, form=form)
    return render_template("group_page.html", )









if __name__ == "__main__":
    app.run(debug=True)
