#!/usr/bin/env python3

from flask_wtf import Form
from wtforms import Form, StringField, PasswordField, SubmitField, validators



class SignUp(Form):
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
