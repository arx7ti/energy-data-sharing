#!/usr/bin/env python3

from models.shared import db
from models.core import Widget
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from sqlalchemy.orm import validates

account_widgets = db.Table(
    "account_widgets",
    db.Model.metadata,
    db.Column("account_id", db.Integer, db.ForeignKey("account.id")),
    db.Column("widget_id", db.Integer, db.ForeignKey("widget.id")),
)


class Account(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(320), unique=True)
    password = db.Column(db.String(255))
    date = db.Column(db.DateTime, default=datetime.now)
    name = db.Column(db.String(255), unique=False)
    widgets = db.relationship("Widget", secondary=account_widgets)

    def check_password(self, password):
        return True if check_password_hash(self.password, password) else False

    def __repr__(self):
        return "<%s>" % self.email


class Household(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255), unique=True)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id", ondelete="CASCADE"))
    # account = db.relationship(
    #     "Account", backref=db.backref("related_account", lazy=True)
    # )
    name = db.Column(db.String(64))
    address = db.Column(db.String(255), default="")

    @validates("name")
    def validate_name(self, key, name):
        assert len(name) > 2, "Household name length must be greater than 2"
        return name

    def __repr__(self):
        return "<%s@%s>" % (self.name, self.address)


class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(
        db.Integer, db.ForeignKey("household.id", ondelete="CASCADE")
    )
    household = db.relationship(
        "Household", backref=db.backref("sensor_household", lazy=True, cascade="all"),
    )
    public_key = db.Column(db.Text, unique=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return "<%s@%s>" % (self.name, self.household.name)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(
        db.Integer, db.ForeignKey("household.id", ondelete="CASCADE")
    )
    household = db.relationship(
        "Household", backref=db.backref("category_household", lazy=True),
    )
    name = db.Column(db.String(64))


# class Appliance(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     household_id = db.Column(db.Integer, db.ForeignKey("household.id"))
#     household = db.relationship(
#         "Household", backref=db.backref("appliance_household", lazy=True)
#     )
#     category = db.Column(db.String(64))
#     name = db.Column(db.String(64))
#     brand = db.Column(db.String(64))
#     power = db.Column(db.Float, default=1.0)

#     def __repr__(self):
#         return "<%s@%s>" % (self.name, self.household.name)
