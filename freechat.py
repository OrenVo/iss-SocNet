#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys  

reload(sys)  
sys.setdefaultencoding('utf8')
################################################################################
# @project Free Chat - IIS2020(Sociální síť: diskuse v diskusních skupinách)
#
# @file freechat.py
# @brief Online message forum
#
# @author Roman Fulla <xfulla00>
################################################################################

from flask import Flask, redirect, render_template, request, url_for
from flaskext.mysql import MySQL

app = Flask(__name__)

login = False
username = "Daniel"
userlastgroup = "home_page"


################################################################################
# Unregistered user pages
################################################################################

@app.route("/")
@app.route('/index/')
@app.route('/welcome/')
def welcome():
    if login is True:
        return redirect(url_for("home"))
    else:
        return render_template("main_page.html")


@app.route("/register/")
@app.route("/registration/")
def register():
    if login is True:
        return redirect(url_for("home"))
    else:
        return render_template("registration_page.html")


@app.route("/visit/")
@app.route("/visitor/")
def visit():
    if login is True:
        return redirect(url_for("home"))
    else:
        return render_template("main_page.html")  # visit_page.html


@app.route("/egg/")
@app.route("/easter/")
@app.route("/easteregg/")
@app.route("/easter_egg/")
def egg():
    return render_template("egg_page.html")


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return "Hic Sunt Dracones"


################################################################################
# User pages
################################################################################

@app.route("/home/")
def home():
    if login is not True:
        return render_template("main_page.html")
    else:
        lastgroup = userlastgroup
        return render_template(lastgroup + ".html")


@app.route("/profile/<name>/")
@app.route("/profiles/<name>/")
@app.route("/user/<name>/")
@app.route("/users/<name>/")
def user(name):
    return render_template("profile_page.html", username=name)


@app.route("/profile/<name>/settings")
@app.route("/profiles/<name>/settings")
@app.route("/user/<name>/settings")
@app.route("/users/<name>/settings")
def settings(name):
    if login is not True or username != name:
        return "YOU ARE TRESSPASSING!"
    else:
        return name + " settings page."


################################################################################
# Group pages
################################################################################

@app.route("/group/<name>/")
@app.route("/groups/<name>/")
def group(name):
    return "This is " + name + " group page."


@app.route("/group/<name>/<topic>")
@app.route("/groups/<name>/<topic>")
def thread(name, topic):
    return "This is " + topic + " in " + name + " group."


if __name__ == "__main__":
    app.run(debug=True)
