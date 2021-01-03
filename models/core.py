#!/usr/bin/env python3


from models.shared import db
from datetime import datetime


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(64), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return "<%s>" % self.name


class Widget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    shortcut = db.Column(db.String(32), unique=True, nullable=False)

    def __repr__(self):
        return "<%s>" % self.name
