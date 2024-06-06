import project.core.app as app
import project.core.utils as utils
import project.core.errors as errors
import project.core.config as config
import project.modules.roles as roles
import project.modules.search as search
import sqlalchemy.orm as orm
import flask
import uuid
import bcrypt
import json
import os
from datetime import timedelta


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
    creation_date: orm.Mapped[str] = orm.mapped_column()
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
            user_id=self.id,
            token=token,
            expires=(utils.now() + timedelta(days=30)).isoformat(),
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
            role = roles.Role.getFromId(role_id)
            if not role:
                continue
            parsed_roles.append(role)

        self.setRoles(parsed_roles)

        return parsed_roles

    def setRoles(self, new_roles):
        raw_roles = []
        for role in new_roles:
            if not role or not role.id or not roles.Role.getFromId(role.id):
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

    def hasAPermission(self, *permissions):
        for permission in permissions:
            if self.hasPermission(permission):
                return True
        return False

    def hasAPermissionOrAbort(self, *permissions):
        if not self.hasAPermission(*permissions):
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


search.SearchEngine(
    User,
    [
        {
            "value": "username",
            "method": search.basic_text,
            "multiplier": 2.0,
        },
        {
            "value": "display_name",
            "method": search.basic_text,
            "multiplier": 2.0,
        },
        {
            "value": "description",
            "method": search.basic_text,
            "multiplier": 1.0,
        },
        {
            "value": "email",
            "method": search.basic_text,
            "multiplier": 1.5,
        },
        {
            "value": "phone",
            "method": search.basic_text,
            "multiplier": 1.5,
        },
        {
            "value": "creation_date",
            "method": search.time_iso,
            "multiplier": 1.0,
        },
    ],
    {
        "type": "User",
        "name": lambda self: self.getNameText(),
        "url": lambda self: "/users/" + str(self.id) + "/",
    },
)


# Create Admin
@app.on_create_all
def create_admin():
    if not app.db.session.execute(
        app.db.select(User).where(User.is_admin == True)
    ).scalar_one_or_none():
        admin_password = config.get_config("ADMIN_PASSWORD")
        assert (
            admin_password
        ), "Please assign a password to the admin account in the config.json file!"

        admin_username = config.get_config("ADMIN_USERNAME")
        assert (
            admin_username
        ), "Please assign a username to the admin account in the config.json file!"

        admin_user = User(
            creation_date=utils.now_iso(),
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


# TODO: Add a page for ManageUser's to edit other's people settings
@app.app.route("/api/users/", methods=["POST"])
@app.app.route("/api/users/<int:id>/", methods=["PUT", "DELETE"])
def create_user(id=None):
    data = app.get_data()

    user = None
    if flask.request.method == "POST":
        user = User()
        user.creation_date = utils.now_iso()
    else:
        user = User.getFromId(id)
    if not user:
        raise errors.InstanceNotFound

    calling_user = User.getFromRequest()
    if flask.request.method != "POST":
        if not calling_user:
            raise errors.exceptions.Unauthorized
        if calling_user and calling_user != user:
            calling_user.hasPermissionOrAbort(roles.Permission.ManageUsers)
            if not calling_user.overseesUser(user):
                raise errors.NeedPermission

    if flask.request.method == "DELETE":
        if user.id == 1:
            return "You cannot delete the admin account.", 403
        app.db.session.delete(user)
        app.db.session.commit()
        return flask.redirect("/users/")

    user.creation_date = utils.now_iso()
    for property_name in ["description", "email", "phone"]:
        if property_name in data:
            property_value = data[property_name]
            if len(property_value) > 200:
                return (
                    "The "
                    + property_name
                    + " cannot exceed a length of 200 characters."
                )
            setattr(user, property_name, property_value)

    if "display_name" in data:
        display_name = data["display_name"]
        if display_name != "":
            if len(display_name) < 3:
                return "Your display name must be at least 3 characters."
            elif len(display_name) > 20:
                return "Your display name cannot exceed 20 characters."
        user.display_name = display_name

    if "username" in data:
        username = data["username"]
        if len(username) < 3:
            return "Your username must be at least 3 characters."
        elif len(username) > 20:
            return "Your username cannot exceed 20 characters."
        user.username = username

    if "username" in data:
        username = data["username"]
        if len(username) < 3:
            return "Your username must be at least 3 characters."
        elif len(username) > 20:
            return "Your username cannot exceed 20 characters."
        user.username = username

    if "password" in data:
        password = data["password"]
        if len(password) < 8:
            return "Your password must be at least 8 characters."
        elif len(password) > 200:
            return "Your password must not be longer than 200 characters."
        user.password = hash(password)

    app.db.session.add(user)
    app.db.session.commit()

    session = user.createSession()
    app.db.session.commit()

    if flask.request.method == "POST":
        response = flask.make_response(flask.redirect("/manage/", code=303))
        response.set_cookie(
            "session",
            session.getRaw(),
            max_age=timedelta(days=30),
            path="/",
            samesite="Strict",
            secure=True,
        )
        return response

    if user == calling_user:
        return flask.redirect("/settings/", code=303)
    return flask.redirect("/users/%d/settings" % user.id)


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

    response = flask.make_response(flask.redirect("/manage/"))
    response.set_cookie(  # TODO BUG: Safari doesn't save cookie (max_age?) Also see other set_cookie
        "session",
        session.getRaw(),
        max_age=timedelta(days=30),
        path="/",
        samesite="Strict",
        secure=True,
    )

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
def user_list():
    users = app.db.session.execute(app.db.select(User).order_by(User.id)).scalars()
    return flask.render_template("/users/index.html", users=users)


@app.app.route("/teams/")
def team_list():
    return flask.render_template(
        "users/teams.html",
        roles=app.db.session.execute(app.db.select(roles.Role)).scalars().all(),
    )


@app.app.route("/users/<int:id>/")
def user_profile(id):
    user = User.getFromId(id)
    if not user:
        raise errors.InstanceNotFound

    calling_user = User.getFromRequest()

    return flask.render_template(
        "users/profile.html",
        user=user,
        calling_user=calling_user,
        roles=app.db.session.execute(app.db.select(roles.Role)).scalars(),
        Permission=roles.Permission,
    )


@app.app.route("/settings/")
@app.app.route("/users/<int:id>/settings/")
def other_settings(id=None):
    if id:
        user = User.getFromId(id)
        if not user:
            raise errors.InstanceNotFound
    else:
        user = User.getFromRequestOrAbort()

    calling_user = User.getFromRequestOrAbort()
    if calling_user != user:
        calling_user.hasPermissionOrAbort(roles.Permission.ManageUsers)
        if not calling_user.overseesUser(user):
            raise errors.NeedPermission

    if id and calling_user == user:
        return flask.redirect("/settings/")

    return flask.render_template(
        "/users/settings.html/", user=user, calling_user=calling_user
    )
