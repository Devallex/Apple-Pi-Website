from project.core.app import app
import flask
import werkzeug
import mimetypes

@app.route("/<path:path>/")
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
    raise werkzeug.exceptions.NotFound


@app.route("/")
def root_page():
    return page("index.html")
