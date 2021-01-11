#!/usr/bin/env python3

import io
from kernel.store import categories
from itertools import chain
import torch
import pandas as pd
import altair as alt
import numpy as np
from numpy import fromstring, float32, frombuffer, asarray
from deep.attentions import Model
from slugify import slugify
from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify,
    abort,
)
from models.shared import db
from models.account import Account, Household, Sensor, Appliance, Category
from models.core import Page, Widget
from models.monitor import Classifier
from forms.core import AddPageForm, AddWidgetForm
from forms.account import (
    SignUpForm,
    LoginForm,
    AddCategoryForm,
    AddHouseholdForm,
    AddSensorForm,
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
    account_categories = Category.query.filter(
        Category.household_id.in_([household.id for household in households])
    )
    context = {
        "households": households,
        "sensors": sensors,
        "categories": account_categories,
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
            account_id=current_user.id,
            slug=slugify(form.name.data),
            name=form.name.data,
            address=form.address.data,
            favorite=form.favorite.data,
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
        category = Category(
            household_id=form.household.data.id,
            household=form.household.data,
            name=form.category.data,
        )
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
            category=form.category.data,
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


model = Model(55)
model.load_state_dict(
    torch.load(
        "../deep-nilm/store/model-attentions-0b48121a1172d2dc1340002503aafcdc.pth"
    )["weights"]
)
model.eval()


@app.route("/push", methods=["POST"])
def push_signal():
    data = request.json["signal"]
    count = request.json["count"]
    public_key = request.json["public_key"]
    # signal = fromstring(data, float32)
    signal = asarray(data, dtype="float32")
    with torch.no_grad():
        output = model(torch.tensor(signal).unsqueeze(0)).squeeze(0).detach().numpy()
    sensor = Sensor.query.filter_by(public_key=public_key).first()
    if not sensor:
        response = {"status": False, "message": "Sensor was not found."}
        return jsonify(response)
    predictions = Classifier(
        sensor_id=sensor.id, sensor=sensor, predictions=output.tostring(),
    )
    db.session.add(predictions)
    db.session.commit()
    response = {"status": True}
    return jsonify(response)


# @app.route("/monitor/<string:household_name>")
# @login_required
# def monitor_household(household_name):
#     return render_template("monitor.html", heading="Monitor", chart=chart)


def render_chart(sensor_id, related_categories_query):
    related_categories = sorted(
        list(map(lambda query: query.name, related_categories_query))
    )
    pointer = [
        index
        for index, category in enumerate(categories.values())
        if category in related_categories
    ]
    predictions = list(
        Classifier.query.filter_by(sensor_id=sensor_id)
        .order_by(Classifier.date.desc())
        .limit(12)
    )[::-1]
    predictions = [
        # np.where(
        fromstring(x.predictions, dtype="float32", count=50 * len(categories)).reshape(
            50, len(categories)
        )[:, pointer]
        #     > 0.19,
        #     1,
        #     0,
        # )
        for x in predictions
    ]
    source = pd.DataFrame(chain(*predictions), columns=related_categories)

    base_chart = (
        alt.Chart(source.reset_index())
        .mark_circle(size=32)
        .transform_fold(fold=related_categories, as_=["categories", "value"])
        .encode(
            x="index:Q",
            y=alt.Y("categories:N", axis=alt.Axis(title=None)),
            # color="value:Q",
            tooltip=[
                alt.Tooltip("value:Q", format=".2f"),
                alt.Tooltip("index:Q", format="d"),
            ],
            color=alt.Color(
                "value:Q",
                scale=alt.Scale(
                    domain=[0, 0.5, 1],
                    # range=["#ffffff", "#e7dcfe", "#cfb9fd", "#ac84fc", "#8950fc"],
                    range=["#ffffff", "#000000"],
                    type="linear",
                ),
                legend=None,
            ),
        )
        .properties(width=625, height=40 * len(related_categories))
        .configure_axis(titleFontSize=14, labelFontSize=14)
        # .configure_view(strokeOpacity=0)
        # .interactive()
        # .configure_legend(orient="bottom", labelFontSize=18, titleFontSize=18)
    )
    selection = alt.selection_single(
        fields=["index"], nearest=True, on="mouseover", empty="none", clear="mouseout"
    )
    return base_chart.to_html() if len(predictions) > 0 else None


@app.route("/monitor", defaults={"household_slug": None})
@app.route("/monitor/<string:household_slug>")
@login_required
def monitor(household_slug):
    # Look up for given household
    if household_slug is not None:
        household_by_query = Household.query.filter_by(
            account_id=current_user.id, slug=household_slug
        ).first()
        # Raise 404 error if does not exist
        if not household_by_query:
            abort(404)

    folds = []
    for household in list(
        Household.query.filter(
            Household.account_id == current_user.id,
            Household.slug != household_by_query.slug,
        )
    ) + [household_by_query]:
        folds += [
            {
                "household_slug": household.slug,
                "household_name": household.name,
                "active": True if household.slug == household_by_query.slug else False,
            }
        ]
    folds = sorted(folds, key=lambda fold: fold["household_name"])

    sensors = {}
    for sensor in Sensor.query.filter_by(household_id=household_by_query.id):
        related_categories_query = Category.query.filter_by(
            household_id=household_by_query.id
        )
        sensors[sensor.name] = {}
        sensors[sensor.name]["chart"] = render_chart(
            sensor.id, related_categories_query
        )

    return render_template(
        "monitor.html", heading="Monitor", folds=folds, sensors=sensors
    )
    # return render_template("monitor.html", heading="Monitor", chart=chart)
    # return redirect(url_for("monitor_household"))


if __name__ == "__main__":
    app.run(debug=True)
