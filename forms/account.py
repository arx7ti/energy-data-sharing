#!/usr/bin/env python3

from flask_login import current_user
from models.account import Account, Household
from flask_wtf import Form
from wtforms import (
    Form,
    StringField,
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
    submit = SubmitField("Register")

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
    submit = SubmitField("Add household")


def get_households():
    return Household.query.filter_by(account_id=current_user.id)


class AddSensorForm(Form):
    name = StringField("Name", [validators.Length(min=2, max=64)])
    household = QuerySelectField("Household", query_factory=get_households)
    public_key = StringField("Public Key")
    submit = SubmitField("Add sensor")
