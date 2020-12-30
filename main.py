#!/usr/bin/env python3

from flask import Flask, render_template
from models.shared import db
from models.account import Account


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://admin:admin@localhost/deepnilm"
db.init_app(app)
with app.app_context():
    db.create_all()


@app.route("/hello/<name>")
def ind(name):
    return "Hello, " + name


if __name__ == "__main__":
    app.run(debug=True)
