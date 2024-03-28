# NOTE: Do not remove unused imports
from app import app, render_template, request
from flask import Flask, send_from_directory
from werkzeug.exceptions import HTTPException


def send(path):
    return send_from_directory("./project/website/static/", path)


def attempt_send(paths):
    for path in paths:
        try:
            return send(path)
        except:
            continue
        break

@app.errorhandler(HTTPException)
def handle_error(error):
    if "text/html" in request.headers.getlist("accept")[0]:
        return render_template(
            "error.html",
            name="Not Found",
            code=error.code,
            description=error.description,
            show_home=True,
        )
    return "Error — " + str(error.code) + "\n\n" + error.description, error.code


@app.route("/<path:path>/")
def page(path):
    while path[-1] == "/":
        path = path[0:-1]
    page = attempt_send([path, path + ".html", path + "/index.html"])
    if page:
        return page
    return render_template(
        "error.html",
        name="Not Found",
        code=404,
        description="The page was not found on the server.",
        show_home=True,
    )


@app.route("/")
def home_page():
    return page("index.html")
