#!/usr/bin/env python3

from kernel.store import categories
from flask_login import current_user
from models.account import Account, Household
from flask_wtf import Form
from wtforms import (
    Form,
    StringField,
    FloatField,
    BooleanField,
    IntegerField,
    PasswordField,
    SelectField,
    SubmitField,
    validators,
    ValidationError,
)
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from werkzeug.security import check_password_hash


class SignUpForm(Form):
    name = StringField("Name", [validators.Length(min=2, max=255)])
    email = StringField("Email", [validators.Length(min=6, max=320)])
    password = PasswordField(
        "Password",
        [
            validators.DataRequired(),
            validators.EqualTo("confirm", message="Passwords must match"),
        ],
    )
    confirm = PasswordField("Confirm password")
    submit = SubmitField("Register")


class LoginForm(Form):
    email = StringField("Email", [validators.DataRequired()])
    password = PasswordField("Password", [validators.DataRequired()])
    submit = SubmitField("Login")

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        email = args[0].get("email", None)
        if email:
            self.account = Account.query.filter_by(email=email).first()
        else:
            self.account = None

    def validate_email(self, field):
        if not self.account:
            raise ValidationError("Account with given Email doesn't exist.")

    def validate_password(self, field):
        if not self.account:
            return None
        if not self.account.check_password(field.data):
            raise ValidationError("Wrong password.")


class AddHouseholdForm(Form):
    name = StringField("Name", [validators.Length(min=2, max=64)])
    address = StringField("Address", [validators.Length(min=6, max=320)])
    # favorite = BooleanField("Favorite")
    submit = SubmitField("Add household")


def get_households():
    return Household.query.filter_by(account_id=current_user.id)


def get_categories():
    return ApplianceCategory.query.all()


class AddSensorForm(Form):
    name = StringField("Name", [validators.Length(min=2, max=64)])
    household = QuerySelectField("Household", query_factory=get_households)
    public_key = StringField("Public Key")
    submit = SubmitField("Add sensor")


class AddCategoryForm(Form):
    household = QuerySelectField("Household", query_factory=get_households)
    category = SelectField("Category", choices=categories.values())
    submit = SubmitField("Add category")


class AddApplianceForm(Form):
    household = QuerySelectField("Household", query_factory=get_households)
    category = SelectField("Category", choices=categories.values())
    name = StringField("Name", [validators.Length(min=2, max=64)])
    brand = StringField("Brand", [validators.Length(min=2, max=64)])
    power = FloatField("Power", [validators.DataRequired()])
    submit = SubmitField("Add appliance")
