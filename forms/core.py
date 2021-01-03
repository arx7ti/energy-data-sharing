#!/usr/bin/env python3


from flask_login import current_user
from flask_wtf import Form
from wtforms import (
    Form,
    StringField,
    FloatField,
    IntegerField,
    PasswordField,
    TextAreaField,
    SelectField,
    SubmitField,
    validators,
    ValidationError,
)
from wtforms.ext.sqlalchemy.fields import QuerySelectField


class AddPageForm(Form):
    name = StringField("Name", [validators.Length(min=2, max=255)])
    content = TextAreaField("Content", [validators.DataRequired()])
    submit = SubmitField("Create page")
