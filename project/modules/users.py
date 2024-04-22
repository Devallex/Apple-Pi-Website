import project.core.app as app
import project.modules.roles as roles
import project.core.utils as utils
import project.core.errors as errors
import sqlalchemy.orm as orm
import flask
import uuid
import bcrypt
import json
import os
from datetime import datetime


def hash(code):
    return bcrypt.hashpw(code.encode("utf8"), bcrypt.gensalt()).decode("utf8")


# Classes
class Session(app.db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    user_id: orm.Mapped[int] = orm.mapped_column()
    token: orm.Mapped[str] = orm.mapped_column()
    expires: orm.Mapped[int] = orm.mapped_column()

    def getRaw(self):
        return str(self.id) + "." + str(self.user_id) + "." + self.token

    def getFromRaw(raw):
        pieces = raw.split(".")
        id, user_id, token = pieces[0], pieces[1], pieces[2]

        return app.db.session.execute(
            app.db.select(Session).where(
                Session.id == id,
                Session.user_id == user_id,
                Session.token == token,
            )
        ).scalar_one_or_none()


class User(app.db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    creation_date: orm.Mapped[float] = orm.mapped_column()
    username: orm.Mapped[str] = orm.mapped_column(unique=True)
    password: orm.Mapped[str] = orm.mapped_column(unique=True)
    roles: orm.Mapped[str] = orm.mapped_column(default="[]")
    is_admin: orm.Mapped[bool] = orm.mapped_column(default=False)
    display_name: orm.Mapped[str] = orm.mapped_column(nullable=True)
    email: orm.Mapped[str] = orm.mapped_column(nullable=True)
    phone: orm.Mapped[str] = orm.mapped_column(nullable=True)
    description: orm.Mapped[str] = orm.mapped_column(nullable=True)

    def getFromId(id: int) -> "User":
        return app.db.session.execute(
            app.db.select(User).where(User.id == id)
        ).scalar_one_or_none()

    def getFromSession(session: Session) -> "User":
        return User.getFromId(session.user_id)

    def getFromRequest() -> "User":
        raw = flask.request.cookies.get("session")
        if not raw:
            return

        session = Session.getFromRaw(raw)
        if not session:
            return

        return User.getFromSession(session)

    def getFromRequestOrAbort() -> "User":
        user = User.getFromRequest()

        if not user:
            raise errors.LoggedOut
        return user

    def createSession(self):
        token = str(uuid.uuid4())  # Session id is unique, so token doesn't need to be

        session = Session(
            user_id=self.id, token=token, expires=utils.timestamp() + 2_592_000
        )
        app.db.session.add(session)

        return session

    def getDisplayName(self):
        return self.display_name or self.username

    def getNameText(self):
        name_text = "@" + self.username
        if self.username != self.display_name and self.display_name:
            name_text = self.display_name + " (" + name_text + ")"
        return name_text

    def getDateText(self):
        return str(datetime.fromtimestamp(self.creation_date))

    # Roles
    def getRolesText(self):
        roles = self.getRoles()
        roles_text = ""
        for role in roles:
            roles_text += role.label + ", "
        return roles_text.removesuffix(", ")

    def getRoles(self):
        parsed_roles = []
        for role_id in json.loads(self.roles or "[]"):
            parsed_roles.append(roles.Role.getFromId(role_id))

        return parsed_roles

    def setRoles(self, roles):
        # TODO: Remove invalid permissions

        raw_roles = []
        for role in roles:
            if not role or not role.id:
                continue
            raw_roles.append(role.id)

        raw_roles.sort()
        self.roles = json.dumps(raw_roles)

    def addRole(self, role):
        roles = self.getRoles()
        if role in roles:
            return
        roles.append(role)
        self.setRoles(roles)

    def removeRole(self, role):
        roles = self.getRoles()
        while role in roles:
            roles.remove(role)
        self.setRoles(roles)

    def hasRole(self, role):
        return role in self.getRoles()

    # Permissions
    def hasPermission(self, permission) -> bool:
        for role in self.getRoles():
            if role.hasPermission(permission):
                return True
        return False

    def hasPermissionOrAbort(self, permission):
        if not self.hasPermission(permission):
            raise errors.NeedPermission

    def getHighestRole(self):
        highest_role = None
        for role in self.getRoles():
            if not highest_role:
                highest_role = role
                continue
            if role.overseesRole(highest_role):
                highest_role = role
        return highest_role

    def overseesRole(self, other_role) -> bool:
        for role in self.getRoles():
            if role.overseesRole(other_role):
                return True
        return False

    def overseesUser(self, user) -> bool:
        highest_role, user_highest_role = self.getHighestRole(), user.getHighestRole()
        if not highest_role:
            return False
        if not user_highest_role:
            return True
        return highest_role.overseesRole(user_highest_role)


# Create Admin
@app.on_create_all
def create_admin():
    if not app.db.session.execute(
        app.db.select(User).where(User.is_admin == True)
    ).scalar_one_or_none():
        admin_password = os.getenv("ADMIN_PASSWORD")
        assert (
            admin_password
        ), "Please assign a password to the admin account in the .env file!"

        admin_username = os.getenv("ADMIN_USERNAME")
        assert (
            admin_username
        ), "Please assign a username to the admin account in the .env file!"

        admin_user = User(
            creation_date=utils.timestamp(),
            username=admin_username,
            password=hash(admin_password),
            roles="[1]",
            is_admin=True,
            display_name=admin_username,
            description="The administrator account for this website.",
        )
        app.db.session.add(admin_user)
        app.db.session.commit()


# API
@app.app.route("/api/users/<int:id>/")
def read_user(id: int):
    user = User.getFromId(id)

    if not user:
        return flask.make_response("A user with that id was not found.", 404)

    return json.dumps(
        {
            "id": user.id,
            "creation_date": user.creation_date,
            "username": user.username,
            "is_admin": user.is_admin,
            "display_name": user.display_name,
            "description": user.description,
        }
    )


@app.app.route("/api/users/", methods=["POST"])
def create_user():
    data = app.get_data()

    user = User(
        creation_date=utils.timestamp(),
        username=data["username"],
        password=hash(data["password"]),
        description="",
        email=data["email"],
        phone=data["phone"],
    )
    app.db.session.add(user)
    app.db.session.commit()

    session = user.createSession()
    app.db.session.commit()

    response = flask.make_response(flask.redirect("/"))
    response.set_cookie("session", session.getRaw(), expires=session.expires, path="/")

    return response


@app.app.route("/api/sessions/", methods=["POST"])
def create_session():
    data = app.get_data()

    user = app.db.session.execute(
        app.db.select(User).where(User.username == data["username"])
    ).scalar_one_or_none()

    if not user:
        return flask.make_response("The provided username does not exist.", 404)

    if not bcrypt.checkpw(
        data["password"].encode("utf8"), user.password.encode("utf8")
    ):
        return flask.make_response("The provided password is incorrect.", 401)

    session = user.createSession()
    app.db.session.commit()

    response = flask.make_response()
    response.set_cookie("session", session.getRaw(), path="/", secure=False)

    return response


@app.app.route("/api/sessions/validate/", methods=["GET"])
def validate_session():
    user = User.getFromRequest()

    if user:
        return json.dumps(True)
    return json.dumps(False)


@app.app.route("/api/sessions/all/", methods=["DELETE"])
def delete_sessions():
    user = User.getFromRequestOrAbort()

    sessions = app.db.session.execute(
        app.db.select(Session).where(Session.user_id == user.id)
    ).scalars()
    for session in sessions:
        app.db.session.delete(session)
    app.db.session.commit()

    response = flask.make_response(flask.redirect("/", code=303))
    response.delete_cookie("session", "/")

    return response


@app.app.route("/api/sessions/", methods=["DELETE"])
def delete_session():
    session = Session.getFromRaw(flask.request.cookies["session"])
    if not session:
        return flask.make_response("You could not be authenticated.", 401)

    app.db.session.delete(session)
    app.db.session.commit()

    response = flask.make_response(flask.redirect("/", code=303))
    response.delete_cookie("session", "/")

    return response


# Pages
@app.app.route("/users/")
@app.app.route("/team/")  # TODO: Give team a separate page which only shows active users
def user_list():
    users = app.db.session.execute(app.db.select(User).order_by(User.id)).scalars()
    return flask.render_template("users/index.html", users=users)


@app.app.route("/users/<int:id>/")
def user_profile(id):
    target_user = User.getFromId(id)
    if not target_user:
        raise errors.InstanceNotFound

    user = User.getFromRequest()

    return flask.render_template(
        "users/profile.html",
        user=user,
        target_user=target_user,
        roles=app.db.session.execute(app.db.select(roles.Role)).scalars(),
        Permission=roles.Permission,
    )


@app.app.route("/settings/")
def settings():
    user = User.getFromRequestOrAbort()

    return flask.render_template("settings.html", user=user)
