#!/usr/bin/env python3

from flask import Flask, render_template, request, flash, redirect, url_for
from models.shared import db
from models.account import Account
from forms.account import SignUpForm, LoginForm
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, login_user, current_user
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash
from wtforms import ValidationError


app = Flask(__name__)
app.secret_key = "something"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://admin:admin@localhost/deepnilm"
login_manager = LoginManager()
db.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app, db)
Bootstrap(app)


@login_manager.user_loader
def get_account(id):
    return Account.query.get(id)

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for("login"))

@app.route("/account", methods=["GET"])
@login_required
def account():
    return render_template("account.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        login_user(form.account)
        return redirect(url_for("account"))
    return render_template("login.html", form=form)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignUpForm(request.form)
    if request.method == "POST" and form.validate():
        password_hash = generate_password_hash(form.password.data)
        account = Account(
            email=form.email.data, name=form.name.data, password=password_hash,
        )
        db.session.add(account)
        db.session.commit()
        login_user(account)
        return redirect(url_for("account"))
    return render_template("signup.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)
