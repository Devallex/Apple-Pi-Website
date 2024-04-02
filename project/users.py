from app import (
    app,
    db,
    request,
    redirect,
    render_template,
    Mapped,
    mapped_column,
    getenv,
    make_response,
    on_create_all,
)

from uuid import uuid4
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime
from json import dumps
from json import dumps, loads
from utils import timestamp


def hash(code):
    return hashpw(code.encode("utf8"), gensalt()).decode("utf8")


# Classes
class Session(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column()
    token: Mapped[str] = mapped_column()
    expires: Mapped[int] = mapped_column()

    def getRaw(self):
        return str(self.id) + "." + str(self.user_id) + "." + self.token

    def getFromRaw(raw):
        pieces = raw.split(".")
        id, user_id, token = pieces[0], pieces[1], pieces[2]

        return db.session.execute(
            db.select(Session).where(
                Session.id == id,
                Session.user_id == user_id,
                Session.token == token,
            )
        ).scalar_one_or_none()


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    creation_date: Mapped[float] = mapped_column()
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column(unique=True)
    roles: Mapped[str] = mapped_column(default="[]")
    is_admin: Mapped[bool] = mapped_column(default=False)
    display_name: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(nullable=True)

    def getFromId(id: int):
        return db.session.execute(
            db.select(User).where(User.id == id)
        ).scalar_one_or_none()

    def getFromSession(session: Session):
        return User.getFromId(session.user_id)

    def getFromRequest():
        raw = request.cookies.get("session")
        if not raw:
            return

        session = Session.getFromRaw(raw)
        if not session:
            return

        return User.getFromSession(session)

    def createSession(self):
        token = str(uuid4())  # Session id is unique, so token doesn't need to be

        session = Session(user_id=self.id, token=token, expires=timestamp() + 2_592_000)
        db.session.add(session)

        return session

    def getNameText(self):
        name_text = "@" + self.username
        if self.username != self.display_name and self.display_name:
            name_text = self.display_name + " (" + name_text + ")"
        return name_text

    def getDateText(self):
        return str(datetime.fromtimestamp(self.creation_date))


# Create Admin
@on_create_all
def create_admin():
    if not db.session.execute(
        db.select(User).where(User.is_admin == True)
    ).scalar_one_or_none():
        admin_password = getenv("ADMIN_PASSWORD")
        assert (
            admin_password
        ), "Please assign a password to the admin account in the .env file!"

        admin_username = getenv("ADMIN_USERNAME")
        assert (
            admin_username
        ), "Please assign a username to the admin account in the .env file!"

        admin_user = User(
            creation_date=timestamp(),
            username=admin_username,
            password=hash(admin_password),
            is_admin=True,
            display_name=admin_username,
            description="The administrator account for this website.",
        )
        db.session.add(admin_user)
        db.session.commit()


# API
@app.route("/api/users/<int:id>/")
def read_user(id: int):
    user = User.getFromId(id)

    if not user:
        return make_response("A user with that id was not found.", 404)

    return dumps(
        {
            "id": user.id,
            "creation_date": user.creation_date,
            "username": user.username,
            "is_admin": user.is_admin,
            "display_name": user.display_name,
            "description": user.description,
        }
    )


@app.route("/api/users/", methods=["POST"])
def create_user():
    data = request.get_json(force=True)

    user = User(
        creation_date=timestamp(),
        username=data["username"],
        password=hash(data["password"]),
        description="",
        email=data["email"],
        phone=data["phone"],
    )
    db.session.add(user)
    db.session.commit()

    session = user.createSession()
    db.session.commit()

    response = make_response(redirect("/"))
    response.set_cookie("session", session.getRaw(), expires=session.expires, path="/")

    return response


@app.route("/api/sessions/", methods=["POST"])
def create_session():
    data = request.get_json(force=True)

    user = db.session.execute(
        db.select(User).where(User.username == data["username"])
    ).scalar_one_or_none()

    if not user:
        return make_response("The provided username does not exist.", 404)

    if not checkpw(data["password"].encode("utf8"), user.password.encode("utf8")):
        return make_response("The provided password is incorrect.", 401)

    session = user.createSession()
    db.session.commit()

    response = make_response(redirect("/"))
    response.set_cookie("session", session.getRaw(), path="/", secure=False)

    return response


@app.route("/api/sessions/validate/", methods=["GET"])
def validate_session():
    user = User.getFromRequest()

    if user:
        return dumps(True)
    return dumps(False)


@app.route("/api/sessions/all/", methods=["DELETE"])
def delete_sessions():
    user = User.getFromRequest()
    if not user:
        return make_response("You could not be authenticated.", 401)

    sessions = db.session.execute(
        db.select(Session).where(Session.user_id == user.id)
    ).scalars()
    for session in sessions:
        print(session)
        db.session.delete(session)
    db.session.commit()

    response = make_response(redirect("/", code=303))
    response.delete_cookie("session", "/")

    return response


@app.route("/api/sessions/", methods=["DELETE"])
def delete_session():
    session = Session.getFromRaw(request.cookies["session"])
    if not session:
        return make_response("You could not be authenticated.", 401)

    db.session.delete(session)
    db.session.commit()

    response = make_response(redirect("/", code=303))
    response.delete_cookie("session", "/")

    return response


# Pages
@app.route("/users/")
def user_list():
    users = db.session.execute(db.select(User).order_by(User.id)).scalars()
    return render_template("users/index.html", users=users)


@app.route("/users/<int:id>/")
def user_profile(id):
    user = User.getFromId(id)
    if not user:
        return make_response("A user with that id was not found.", 404)

    return render_template(
        "users/profile.html",
        user=user,
    )


@app.route("/settings/")
def settings():
    user = User.getFromRequest()
    if not user:
        return make_response("You could not be authenticated.", 401)

    return render_template("settings.html", user=user)
