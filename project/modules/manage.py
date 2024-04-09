import project.core.app as app
import project.modules.users as users
import flask


@app.app.route("/manage/")
def page_manage():
    user = users.User.getFromRequestOrAbort()

    return flask.render_template("manage.html", user=user)
