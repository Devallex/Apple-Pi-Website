import apscheduler.schedulers
import apscheduler.schedulers.background
import flask
import flask_sqlalchemy
import flask_cors
import sqlalchemy
import apscheduler
import dotenv
import os
import requests
import logging
from werkzeug.middleware.proxy_fix import ProxyFix

if os.path.exists("log.txt"):
    os.remove("log.txt")

dotenv.load_dotenv()

app = flask.Flask("ApplePiWebsite", template_folder="./project/website")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["UPLOAD_FOLDER"] = "./instance/"

templates = []


def add_template(template):
    templates.append(template)


@app.context_processor
def set_template_globals():
    variables = {}

    for template in templates:
        for sub_key, sub_value in template().items():
            variables[sub_key] = sub_value

    return variables


class Base(sqlalchemy.orm.DeclarativeBase):
    pass


db = flask_sqlalchemy.SQLAlchemy(model_class=Base)
db.init_app(app)

flask_cors.CORS(app, support_credentials=False)

scheduler = apscheduler.schedulers.background.BackgroundScheduler()

on_create_all_callbacks = []


def on_create_all(callback):
    on_create_all_callbacks.append(callback)


last_ip = None
domain = os.getenv("DUCKDNS_DOMAIN")
token = os.getenv("DUCKDNS_TOKEN")


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

    mode = os.getenv("MODE")
    assert mode in (
        "dev",
        "debug",
        "prod",
    ), "You must specify the MODE in the .env file!"
    if mode == "prod":
        domain = os.getenv("DUCKDNS_DOMAIN")
        token = os.getenv("DUCKDNS_TOKEN")

        if domain and token:
            print("DuckDNS is enabled for domain '%s'." % domain)
            scheduler.add_job(update_ip, "interval", seconds=10)
            update_ip()

        from waitress import serve

        print(
            "Use password '%s' to log into the '%s' account."
            % (os.getenv("ADMIN_PASSWORD"), os.getenv("ADMIN_USERNAME"))
        )

        if os.getenv("PROD_PROXY") == "true":
            print("Proxy is enabled. This is dangerous if not actually using a proxy!")
            app.wsgi_app = ProxyFix(
                app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
            )
        else:
            print("Proxy is disabled. If using a proxy, enable it in .env.")

        print(
            "Running production server on http://%s:%s, press CTRL/CMD + C to exit."
            % (os.getenv("PROD_HOST"), os.getenv("PROD_PORT"))
        )

        print()

        logger = logging.getLogger("waitress")
        logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler("log.txt")
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)

        serve(app, host=os.getenv("PROD_HOST"), port=os.getenv("PROD_PORT"))
    else:
        app.run(debug=mode == "debug")


def get_data():
    if (
        "application/x-www-form-urlencoded" in flask.request.content_type
        or "multipart/form-data" in flask.request.content_type
    ):
        return flask.request.form

    return flask.request.get_json()
