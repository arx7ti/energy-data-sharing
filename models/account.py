#!/usr/bin/env python3

from models.shared import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash

class Account(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(320), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    name = db.Column(db.String(255), unique=False, nullable=False)

    def check_password(self, password):
        return True if check_password_hash(self.password, password) else False
        

    def __repr__(self):
        return "<%s>" % self.email


class Household(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    account = db.relationship("Account", backref=db.backref("accounts", lazy=True))
    name = db.Column(db.String(64), nullable=False)
    # region_id = db.Column(db.Integer, db.ForeignKey("region.id"), nullable=False)
    # region = db.relationship("Region", backref=db.backref("regions", lazy=True))
    # city_id = db.Column(db.Integer, db.ForeignKey("city.id"), nullable=False)
    # city = db.relationship("City", backref=db.backref("cities", lazy=True))
    address = db.Column(db.String(255), nullable=True, default="")

    def __repr__(self):
        return "<%s@%s>" % (self.name, self.account.email)


class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    # household = db.relationship(
    #     "Household", backref=db.backref("sensor_households", lazy=True)
    # )
    public_key = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return "<%s@%s>" % (self.name, self.household.name)


class ApplianceCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return "<%s>" % self.name


class Appliance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    # household = db.relationship(
    #     "Household", backref=db.backref("appliance_households", lazy=True)
    # )
    category_id = db.Column(
        db.Integer, db.ForeignKey("appliance_category.id"), nullable=False
    )
    category = db.relationship(
        "ApplianceCategory", backref=db.backref("categories", lazy=True)
    )
    name = db.Column(db.String(64), nullable=False)
    brand = db.Column(db.String(64), nullable=False)
    power = db.Column(db.Float, nullable=True, default=1.0)

    def __repr__(self):
        return "<%s@%s>" % (self.name, self.household.name)
