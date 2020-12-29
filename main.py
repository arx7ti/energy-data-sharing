#!/usr/bin/env python3

from flask import Flask, render_template

app = Flask(__name__)


@app.route("/hello/<name>")
def ind(name):
    return "Hello, " + name


if __name__ == "__main__":
    app.run(debug=True)
