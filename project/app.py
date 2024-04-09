from flask import Flask, request, render_template, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from os import getenv
import requests

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


last_ip = None
domain = getenv("DUCKDNS_DOMAIN")
token = getenv("DUCKDNS_TOKEN")


def update_ip():
    global last_ip

    current_ip = requests.get("https://api.ipify.org").content.decode("utf8")
    if current_ip != last_ip:
        print(
            "IP change detected! Old IP is '%s', new IP is '%s'."
            % (last_ip, current_ip)
        )
        last_ip = current_ip
        requests.get(
            "https://www.duckdns.org/update/%s/%s/%s" % (domain, token, current_ip)
        )


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
        domain = getenv("DUCKDNS_DOMAIN")
        token = getenv("DUCKDNS_TOKEN")

        if domain and token:
            print("DuckDNS is enabled for domain '%s'." % domain)
            scheduler.add_job(update_ip, "interval", seconds=10)
            update_ip()

        from waitress import serve

        print(
            "Use password '%s' to log into the '%s' account."
            % (getenv("ADMIN_PASSWORD"), getenv("ADMIN_USERNAME"))
        )
        print(
            "Running production server on %s:%s, press CTRL/CMD + C to exit."
            % (getenv("PROD_HOST"), getenv("PROD_PORT"))
        )
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
