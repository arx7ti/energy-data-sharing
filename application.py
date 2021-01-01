#!/usr/bin/env python3

from flask import Flask, render_template, request, flash, redirect, url_for
from models.shared import db
from models.account import Account
from forms.account import SignUp
from flask_migrate import Migrate
from flask_login import LoginManager, login_user
from flask_bootstrap import Bootstrap


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

@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignUp(request.form)
    if request.method == "POST" and form.validate():
        account = Account(
            email=form.email.data, name=form.name.data, password=form.password.data
        )
        db.session.add(account)
        db.session.commit()
        login_user(account)
        return redirect(url_for("login"))
    return render_template("signup.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)
