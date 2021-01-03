#!/usr/bin/env python3

import altair as alt
from slugify import slugify
from flask import Flask, render_template, request, flash, redirect, url_for
from models.shared import db
from models.account import Account, Household, Sensor, ApplianceCategory, Appliance
from models.core import Page, Widget
from forms.core import AddPageForm, AddWidgetForm
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
    return render_template("form.html", heading="Login", form=form)


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
    return render_template("form.html", heading="Sing Up", form=form)


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
    return render_template("form.html", heading="Add Household", form=form)


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
    return render_template("form.html", heading="Add Sensor", form=form)


@app.route("/account/add-category", methods=["GET", "POST"])
@login_required
def add_category():
    form = AddCategoryForm(request.form)
    if request.method == "POST" and form.validate():
        category = ApplianceCategory(name=form.name.data,)
        db.session.add(category)
        db.session.commit()
        return redirect(url_for("account"))
    return render_template("form.html", heading="Add Category", form=form)


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
    return render_template("form.html", heading="Add Appliance", form=form)


@app.route("/page/<string:slug>")
def page(slug):
    page = Page.query.filter_by(slug=slug).first()
    return render_template("page.html", heading=page.name, content=page.content)


@app.route("/add-page", methods=["GET", "POST"])
@login_required
def add_page():
    form = AddPageForm(request.form)
    if request.method == "POST" and form.validate():
        slug = slugify(form.name.data)
        page = Page(slug=slug, name=form.name.data, content=form.content.data,)
        db.session.add(page)
        db.session.commit()
        return redirect(url_for("page", slug=slug))
    return render_template("form.html", heading="Add Page", form=form)


@app.route("/extensions")
@login_required
def extensions():
    widgets = Widget.query.all()
    heading = "Extensions"
    return render_template("extensions.html", heading=heading, widgets=widgets)


@app.route("/widget/<string:slug>")
@login_required
def widget(slug):
    widget = Widget.query.filter_by(slug=slug).first()
    heading = widget.name
    return render_template("widget.html", heading=heading, widget=widget)


@app.route("/widget/install-widget/<int:widget_id>")
@login_required
def install_widget(widget_id):
    widget = Widget.query.get(widget_id)
    current_user.widgets.append(widget)
    db.session.add(widget)
    db.session.commit()
    return redirect(url_for("widget", slug=widget.slug))


@app.route("/widget/uninstall-widget/<int:widget_id>")
@login_required
def uninstall_widget(widget_id):
    widget = Widget.query.get(widget_id)
    current_user.widgets.remove(widget)
    db.session.commit()
    return redirect(url_for("widget", slug=widget.slug))


@app.route("/add-widget", methods=["GET", "POST"])
@login_required
def add_widget():
    form = AddWidgetForm(request.form)
    if request.method == "POST" and form.validate():
        slug = slugify(form.name.data)
        widget = Widget(
            slug=slug,
            name=form.name.data,
            shortcut=form.shortcut.data,
            description=form.description.data,
        )
        db.session.add(widget)
        db.session.commit()
        return redirect(url_for("extensions"))
    return render_template("form.html", heading="Add Widget", form=form)


@app.route("/monitor")
@login_required
def monitor():
    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(
        type="single", nearest=True, on="mouseover", fields=["date"], empty="none"
    )

    # The basic line
    line = (
        alt.Chart()
        .mark_line(interpolate="basis")
        .encode(
            alt.X("date:T", axis=alt.Axis(title="")),
            alt.Y("price:Q", axis=alt.Axis(title="", format="$f")),
            color="symbol:N",
        )
    )

    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = (
        alt.Chart()
        .mark_point()
        .encode(x="date:T", opacity=alt.value(0),)
        .add_selection(nearest)
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align="left", dx=5, dy=-5).encode(
        text=alt.condition(nearest, "price:Q", alt.value(" "))
    )

    # Draw a rule at the location of the selection
    rules = (
        alt.Chart()
        .mark_rule(color="gray")
        .encode(x="date:T",)
        .transform_filter(nearest)
    )

    # Put the five layers into a chart and bind the data
    stockChart = alt.layer(
        line,
        selectors,
        points,
        rules,
        text,
        data="https://raw.githubusercontent.com/altair-viz/vega_datasets/master/vega_datasets/_data/stocks.csv",
        width=600,
        height=300,
        title="Stock History",
    )
    return render_template(
        "monitor.html", heading="Monitor", chart=stockChart.to_html()
    )


if __name__ == "__main__":
    app.run(debug=True)
