#!/usr/bin/env python3

from models.shared import db


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(320), unique=True, nullable=False)
    password = db.Column(db.String(32), nullable=False)

    def __repr__(self):
        return "<%s>" % self.email
