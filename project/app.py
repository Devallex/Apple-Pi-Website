from flask import Flask, request, render_template, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from os import getenv

load_dotenv()


class Base(DeclarativeBase):
    pass


app = Flask("ApplePiWebsite", template_folder="./project/website")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["UPLOAD_FOLDER"] = "./instance/"

db = SQLAlchemy(model_class=Base)
db.init_app(app)

CORS(app, support_credentials=False)

scheduler = BackgroundScheduler()

on_create_all_callbacks = []


def on_create_all(callback):
    on_create_all_callbacks.append(callback)


def run():
    with app.app_context():
        db.create_all()
        for callback in on_create_all_callbacks:
            callback()
    scheduler.start()

    mode = getenv("MODE")
    assert mode in (
        "dev",
        "debug",
        "prod",
    ), "You must specify the MODE in the .env file!"
    if mode == "prod":
        from waitress import serve
        print("Running production server on %s:%s, press CTRL/CMD + C to exit." % (getenv("PROD_HOST"), getenv("PROD_PORT")))
        print("Use password '%s' to log into the '%s' account." % (getenv("ADMIN_PASSWORD"), getenv("ADMIN_USERNAME")))
        print()
        serve(app, host=getenv("PROD_HOST"), port=getenv("PROD_PORT"))
    else:
        app.run(debug=mode == "debug")


def get_data():
    if (
        "application/x-www-form-urlencoded" in request.content_type
        or "multipart/form-data" in request.content_type
    ):
        return request.form

    return request.get_json()
