import project.core.app as app
import project.modules.users as users
import project.modules.roles as roles
import project.core.errors as errors
import project.core.utils as utils
import sqlalchemy.orm as orm
import urllib.parse as parse
from datetime import datetime
import werkzeug
import os
import flask

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "mp3", "webm", "mp4"}

os.makedirs("instance/media", exist_ok=True)


class Media(app.db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    creation_date: orm.Mapped[float] = orm.mapped_column()
    creator_id: orm.Mapped[int] = orm.mapped_column()
    name: orm.Mapped[str] = orm.mapped_column(unique=True)
    extension: orm.Mapped[str] = orm.mapped_column()
    title: orm.Mapped[str] = orm.mapped_column(nullable=True)
    caption: orm.Mapped[str] = orm.mapped_column(nullable=True)

    def getAll():
        return app.db.session.execute(app.db.select(Media)).scalars().all()

    def getByName(name):
        return app.db.session.execute(
            app.db.select(Media).where(Media.name == name)
        ).scalar_one_or_none()

    def getCreator(self):
        return users.User.getFromId(self.creator_id)

    def getDateText(self):
        return str(datetime.fromtimestamp(self.creation_date))

    def getFile(self):
        return flask.send_from_directory(
            "instance/media/", self.name + "." + self.extension
        )

    def getEncodedName(self):
        return parse.quote_plus(self.name)


# API
@app.app.route("/api/media/", methods=["POST"])
def api_create_media():
    data = app.get_data()
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(roles.Permission.EditMedia)

    if "upload" not in flask.request.files:
        return "You must provide a file to upload.", 400

    upload = flask.request.files["upload"]
    filename = werkzeug.utils.secure_filename(upload.filename).lower()

    name = filename.rsplit(".", 1)[0]
    extension = "." in filename and filename.rsplit(".", 1)[1]
    if not extension or not extension in ALLOWED_EXTENSIONS:
        return (
            "The provided file has an invalid type. You may only use:\n"
            + str(ALLOWED_EXTENSIONS)
            .replace("'", "")
            .replace("{", "")
            .replace("}", ""),
            400,
        )

    # TODO: Validate for reasonable size, spam
    # TODO: Check for duplicate files

    number = 1
    while app.db.session.execute(
        app.db.select(Media).where(Media.name == name + " (" + str(number) + ")")
    ).scalar_one_or_none():
        number += 1
    name = name + " (" + str(number) + ")"

    media = Media(
        creation_date=utils.timestamp(),
        creator_id=user.id,
        name=name,
        extension=extension,
        title=data["title"],
        caption=data["caption"],
    )

    upload.save(
        os.path.join(app.config["UPLOAD_FOLDER"] + "media/", name + "." + extension)
    )

    app.db.session.add(media)
    app.db.session.commit()

    return flask.redirect("/media/" + media.getEncodedName() + "/")


# Files
@app.app.route("/media/<string:name>/raw/")
def file_view_media(name):
    return Media.getByName(parse.unquote_plus(name)).getFile() or (
        "This file was not found on the server.",
        404,
    )


# Pages
@app.app.route("/media/new/")
def page_create_media():
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(roles.Permission.EditMedia)

    return flask.render_template("media/new.html")


@app.app.route("/media/")
def page_view_media_gallery():
    return flask.render_template(
        "media/index.html",
        Media=Media,
        user=users.User.getFromRequest(),
        Permission=roles.Permission,
    )


@app.app.route("/media/<string:name>/")
def page_profile_media(name):
    media = Media.getByName(parse.unquote_plus(name))
    if not media:
        raise errors.InstanceNotFound

    return flask.render_template(
        "media/profile.html",
        media=media,
        creator=media.getCreator(),
        raw_url="/media/" + media.getEncodedName() + "/raw/",
    )
