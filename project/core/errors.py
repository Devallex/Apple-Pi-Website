from project.core.app import app
from flask import render_template, request
import werkzeug.exceptions as exceptions


class LoggedOut(exceptions.HTTPException):
    name = "Logged Out"
    description = "You must be logged in to access this resource."
    code = 401


class NeedPermission(exceptions.HTTPException):
    name = "Need Permission"
    description = "Your account does not have permissions to access this resource. Please request a higher role from someone with access."
    code = 403


class InstanceNotFound(exceptions.HTTPException):
    name = "Instance Not Found"
    description = "You are at at the right URL, but no instance of this type was found on the server. It may have been deleted, or never was created."
    code = 404


@app.errorhandler(LoggedOut)
def handle_unauthorized(error):
    if "text/html" in request.headers.getlist("accept")[0]:
        return render_template(
            "/error.html",
            name=error.name,
            code=error.code,
            description=error.description + " Try <a href='/login/'>logging in</a>.",
            show_home=True,
            show_breadcrumbs=True,
        )
    return "Error — " + str(error.code) + "\n\n" + error.description, error.code


@app.errorhandler(404)
@app.errorhandler(InstanceNotFound)
def handle_not_found(error):
    if "text/html" in request.headers.getlist("accept")[0]:
        return render_template(
            "/error.html",
            name=error.name,
            code=error.code,
            description=error.description,
            show_home=True,
            show_search=True,
            show_breadcrumbs=False,
        )
    return "Error — " + str(error.code) + "\n\n" + error.description, error.code


@app.errorhandler(exceptions.HTTPException)
def handle_error(error):
    if "text/html" in request.headers.getlist("accept")[0]:
        return render_template(
            "/error.html",
            name=error.name,
            code=error.code,
            description=error.description,
            show_home=True,
            show_search=False,
            show_breadcrumbs=True,
        )
    return "Error — " + str(error.code) + "\n\n" + error.description, error.code
