from app import (
    app,
    db,
    Mapped,
    mapped_column,
    request,
    render_template,
    get_data,
    redirect,
)
from datetime import datetime
from users import User
from roles import Permission
from werkzeug.utils import secure_filename
from werkzeug.exceptions import NotFound
from os import path, makedirs
from flask import send_from_directory
from uuid import uuid4
from utils import timestamp
from urllib.parse import quote_plus, unquote_plus

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "mp3", "webm", "mp4"}

makedirs("instance/media", exist_ok=True)


class Media(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    creation_date: Mapped[float] = mapped_column()
    creator_id: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column(unique=True)
    extension: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column(nullable=True)
    caption: Mapped[str] = mapped_column(nullable=True)

    def getAll():
        return db.session.execute(db.select(Media)).scalars().all()

    def getByName(name):
        return db.session.execute(
            db.select(Media).where(Media.name == name)
        ).scalar_one_or_none()

    def getCreator(self):
        return User.getFromId(self.creator_id)

    def getDateText(self):
        return str(datetime.fromtimestamp(self.creation_date))

    def getFile(self):
        return send_from_directory(
            app.config["UPLOAD_FOLDER"] + "media/", self.name + "." + self.extension
        )

    def getEncodedName(self):
        return quote_plus(self.name)


# API
@app.route("/api/media/", methods=["POST"])
def api_create_media():
    data = get_data()
    user = User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(Permission.EditMedia)

    if "upload" not in request.files:
        return "You must provide a file to upload.", 400

    upload = request.files["upload"]
    filename = secure_filename(upload.filename).lower()

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
    while db.session.execute(
        db.select(Media).where(Media.name == name + " (" + str(number) + ")")
    ).scalar_one_or_none():
        number += 1
    name = name + " (" + str(number) + ")"

    media = Media(
        creation_date=timestamp(),
        creator_id=user.id,
        name=name,
        extension=extension,
        title=data["title"],
        caption=data["caption"],
    )

    upload.save(
        path.join(app.config["UPLOAD_FOLDER"] + "media/", name + "." + extension)
    )

    db.session.add(media)
    db.session.commit()

    return redirect("/media/" + media.getEncodedName() + "/")


# Files
@app.route("/media/<string:name>/raw/")
def file_view_media(name):
    return Media.getByName(unquote_plus(name)).getFile() or (
        "This file was not found on the server.",
        404,
    )


# Pages
@app.route("/media/new/")
def page_create_media():
    user = User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(Permission.EditMedia)

    return render_template("media/new.html")


@app.route("/media/")
def page_view_media_gallery():
    return render_template(
        "media/index.html",
        Media=Media,
        user=User.getFromRequest(),
        Permission=Permission,
    )


@app.route("/media/<string:name>/")
def page_profile_media(name):
    media = Media.getByName(unquote_plus(name))
    if not media:
        raise NotFound

    return render_template(
        "media/profile.html",
        media=media,
        creator=media.getCreator(),
        raw_url="/media/" + media.getEncodedName() + "/raw/",
    )
