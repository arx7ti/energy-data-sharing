#!/usr/bin/env python3

from models.shared import db
from datetime import datetime


class Classifier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey("sensor.id"), nullable=False)
    sensor = db.relationship(
        "Sensor", backref=db.backref("classifier_sensor", lazy=True)
    )
    predictions = db.Column(db.LargeBinary, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    # category_id = db.Column(
    #     db.Integer, db.ForeignKey("appliance_category.id"), nullable=False
    # )
