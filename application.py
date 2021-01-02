#!/usr/bin/env python3

from flask import Flask, render_template, request, flash, redirect, url_for
from models.shared import db
from models.account import Account, Household, Sensor, ApplianceCategory, Appliance
from forms.account import (
    SignUpForm,
    LoginForm,
    AddHouseholdForm,
    AddSensorForm,
    AddCategoryForm,
    AddApplianceForm,
)
from flask_migrate import Migrate
from flask_login import (
    LoginManager,
    login_required,
    login_user,
    logout_user,
    current_user,
)
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

# with app.app_context():
#     db.create_all()


@login_manager.user_loader
def get_account(id):
    return Account.query.get(id)


@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for("login"))


@app.route("/account", methods=["GET"])
@login_required
def account():
    households = Household.query.filter_by(account_id=current_user.id).all()
    sensors = Sensor.query.filter(
        Sensor.household_id.in_([household.id for household in households])
    )
    categories = ApplianceCategory.query.all()
    appliances = Appliance.query.filter(
        Appliance.household_id.in_([household.id for household in households])
    )
    context = {
        "households": households,
        "sensors": sensors,
        "categories": categories,
        "appliances": appliances,
    }
    return render_template("account.html", **context)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("account"))
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        login_user(form.account)
        return redirect(url_for("account"))
    return render_template("login.html", form=form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("account"))
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


@app.route("/account/add-household", methods=["GET", "POST"])
@login_required
def add_household():
    form = AddHouseholdForm(request.form)
    if request.method == "POST" and form.validate():
        household = Household(
            account_id=current_user.id, name=form.name.data, address=form.address.data,
        )
        db.session.add(household)
        db.session.commit()
        return redirect(url_for("account"))
    return render_template("add_household.html", form=form)


@app.route("/account/add-sensor", methods=["GET", "POST"])
@login_required
def add_sensor():
    form = AddSensorForm(request.form)
    if request.method == "POST" and form.validate():
        sensor = Sensor(
            household_id=form.household.data.id,
            name=form.name.data,
            public_key=form.public_key.data,
        )
        db.session.add(sensor)
        db.session.commit()
        return redirect(url_for("account"))
    return render_template("add_sensor.html", form=form)


@app.route("/account/add-category", methods=["GET", "POST"])
@login_required
def add_category():
    form = AddCategoryForm(request.form)
    if request.method == "POST" and form.validate():
        category = ApplianceCategory(name=form.name.data,)
        db.session.add(category)
        db.session.commit()
        return redirect(url_for("account"))
    return render_template("add_category.html", form=form)


@app.route("/account/add-appliance", methods=["GET", "POST"])
@login_required
def add_appliance():
    form = AddApplianceForm(request.form)
    if request.method == "POST" and form.validate():
        appliance = Appliance(
            household_id=form.household.data.id,
            category_id=form.category.data.id,
            name=form.name.data,
            brand=form.brand.data,
            power=form.power.data,
        )
        db.session.add(appliance)
        db.session.commit()
        return redirect(url_for("account"))
    return render_template("add_appliance.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)
