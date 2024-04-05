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
    get_data,
)

from uuid import uuid4
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime
from json import dumps, loads
import roles
from utils import timestamp
from pages import LoggedOut, NeedPermission


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

    def getFromRequestOrAbort():
        user = User.getFromRequest()

        if not user:
            raise LoggedOut
        return user

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

    # Roles
    def getRolesText(self):
        roles = self.getRoles()
        roles_text = ""
        for role in roles:
            roles_text += role.label + ", "
        return roles_text.removesuffix(", ")

    def getRoles(self):
        parsed_roles = []
        for role_id in loads(self.roles or "[]"):
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
        self.roles = dumps(raw_roles)

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
                print(role, permission)
                return True
        return False

    def hasPermissionOrAbort(self, permission):
        if not self.hasPermission(permission):
            raise NeedPermission

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
            roles="[1]",
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
    data = get_data()

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
    data = get_data()

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
    user = User.getFromRequestOrAbort()

    sessions = db.session.execute(
        db.select(Session).where(Session.user_id == user.id)
    ).scalars()
    for session in sessions:
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
    target_user = User.getFromId(id)
    if not target_user:
        return make_response("A user with that id was not found.", 404)

    user = User.getFromRequest()

    return render_template(
        "users/profile.html",
        user=user,
        target_user=target_user,
        roles=db.session.execute(db.select(roles.Role)).scalars(),
        Permission=roles.Permission,
    )


@app.route("/settings/")
def settings():
    user = User.getFromRequestOrAbort()

    return render_template("settings.html", user=user)
