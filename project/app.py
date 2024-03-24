import flask
from flask import Flask, request, render_template, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler


class Base(DeclarativeBase):
    pass


app = Flask("ApplePiWebsite", template_folder="./project/website")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

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
    app.run()  # TODO: Fix issue with error when starting in debug mode
