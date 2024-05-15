import werkzeug.exceptions
import project.core.app as app
import project.core.errors as errors
import project.modules.users as users
import project.modules.roles as roles
import project.modules.articles as articles
import flask
import werkzeug
import mimetypes
import re
import json
import requests


@app.app.route("/<path:path>/")
def page(path):
    for sub_path in ("", ".html", "/index.html"):
        final_path = werkzeug.security.safe_join("/static/", path + sub_path)

        try:
            if final_path.endswith(".html"):
                return flask.render_template(final_path)
            else:
                return flask.send_file(
                    "./project/website" + final_path,
                    mimetype=mimetypes.guess_type(final_path)[0],
                )
        except:
            pass

    article = app.db.session.execute(
        app.db.select(articles.Article).where(
            path and articles.Article.path and articles.Article.path == path
        )
    ).scalar_one_or_none()

    if article:
        user = users.User.getFromRequest()

        if not article.is_published:
            if not user:
                raise errors.LoggedOut
            user.hasAPermissionOrAbort(
                roles.Permission.EditArticles, roles.Permission.PreviewArticles
            )

        return flask.render_template(
            "wild_article.html",
            id=article.id,
            is_published=article.is_published,
            title=article.title,
            body=article.body,
            user=user,
            Permission=roles.Permission,
        )

    raise werkzeug.exceptions.NotFound


@app.app.route("/")
def root_page():
    return page("index.html")
