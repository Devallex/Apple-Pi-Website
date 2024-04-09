import apscheduler.schedulers
import apscheduler.schedulers.background
import flask
import flask_sqlalchemy
import flask_cors
import sqlalchemy
import apscheduler
import dotenv
import os

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


def run():
    with app.app_context():
        db.create_all()
        for callback in on_create_all_callbacks:
            callback()
    scheduler.start()
    app.run(
        debug=os.getenv("DEBUG") == "true"
    )  # TODO: Fix issue with error when starting in debug mode


def get_data():
    if (
        "application/x-www-form-urlencoded" in flask.request.content_type
        or "multipart/form-data" in flask.request.content_type
    ):
        return flask.request.form

    return flask.request.get_json()
