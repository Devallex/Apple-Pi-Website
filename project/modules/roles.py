import project.core.app as app
import project.modules.users as users
import project.core.utils as utils
import project.core.errors as errors
import flask
import sqlalchemy.orm as orm
from datetime import datetime
import os
import enum
import json

Permission = enum.Enum(
    "Permission",
    [
        "ManageRoles",
        "AssignRoles",
        "PreviewDocuments",
        "EditDocuments",
        "EditMedia",
    ],
)


class Role(app.db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    parent_id: orm.Mapped[int] = orm.mapped_column(nullable=True)
    creation_date: orm.Mapped[float] = orm.mapped_column()
    label: orm.Mapped[str] = orm.mapped_column(unique=True)
    permissions: orm.Mapped[str] = orm.mapped_column(default="[]")
    description: orm.Mapped[str] = orm.mapped_column(nullable=True)

    def getFromId(id: int):
        return app.db.session.execute(
            app.db.select(Role).where(Role.id == id)
        ).scalar_one_or_none()

    def getRootRole():
        return Role.getFromId(1)

    def getUsers(self):
        all_users = []
        for user in app.db.session.execute(app.db.select(users.User)).scalars():
            if self in user.getRoles():
                all_users.append(user)
        return all_users

    def getParentRole(self):
        if self.parent_id == None:
            return None

        return Role.getFromId(self.parent_id)

    def formatLabel(label):
        label = label.lower()

        while "_" in label:
            label = label.replace("_", "-")
        while " " in label:
            label = label.replace(" ", "-")
        while "--" in label:
            label = label.replace("--", "-")

        return label

    def getDateText(self):
        return str(datetime.fromtimestamp(self.creation_date))

    def getChildRoles(self):
        return app.db.session.execute(
            app.db.select(Role).where(Role.parent_id == self.id)
        ).scalars()

    def getPermissions(self):
        permissions = []
        for permission_name in json.loads(self.permissions):
            permissions.append(Permission[permission_name])
        return permissions

    def setPermissions(self, permissions):
        # TODO: Remove invalid permissions

        raw_permissions = []
        for permission in permissions:
            raw_permissions.append(permission.name)
        self.permissions = json.dumps(raw_permissions)

    def hasPermission(self, permission: Permission):
        return permission in self.getPermissions()

    def overseesRole(self, role) -> bool:
        parent_role = role
        while parent_role:
            parent_role = parent_role.getParentRole()
            if parent_role == self:
                return True
        return False


# Create Admin
@app.on_create_all
def create_admin():
    if not Role.getRootRole():
        label = Role.formatLabel(os.getenv("ADMIN_USERNAME"))

        permissions = []
        for permission_item in Permission:
            permissions.append(permission_item.name)

        root_role = Role(
            creation_date=utils.timestamp(),
            label=label,
            permissions=json.dumps(permissions),
            description="The role reserved for the administrator account.",
        )

        app.db.session.add(root_role)
        app.db.session.commit()


# API
@app.app.route("/api/roles/", methods=["POST"])
def api_create_role():
    user = users.User.getFromRequestOrAbort()
    if not user.hasPermission(Permission.ManageRoles):
        return "You do not have permission to manage roles.", 403

    # TODO: Validate label properly
    # TODO: Validate parent

    data = app.get_data()

    parent = Role.getFromId(int(data["parent"]))
    if not parent:
        return "The parent supplied does not exist.", 404
    if not user.overseesRole(parent) and not user.hasRole(parent):
        return (
            "Your account does not oversee or have the parent role, and therefore cannot create a child role.",
            403,
        )

    permissions = []
    for permission in Permission:
        if not "permission-" + permission.name in data:
            continue
        if not user.hasPermission(permission):
            continue
        if data["permission-" + permission.name] == "on":
            permissions.append(permission.name)

    role = Role(
        parent_id=parent.id,
        creation_date=utils.timestamp(),
        label=Role.formatLabel(data["label"]),
        permissions=json.dumps(permissions),
        description=data["description"],
    )

    app.db.session.add(role)
    app.db.session.commit()

    return flask.redirect("/roles/" + str(role.id) + "/")


@app.app.route("/api/users/<int:user_id>/roles/", methods=["PATCH"])
def api_user_patch_role(user_id):
    data = app.get_data()

    user = users.User.getFromRequestOrAbort()
    if not user.hasPermission(Permission.AssignRoles):
        return "You do not have permission to assign roles.", 403

    target_user = users.User.getFromId(user_id)
    if not target_user:
        return "A user with that id was not found on the server.", 404

    role_id = data["role_id"]
    if not role_id:
        return "You must specify a role to assign.", 400

    target_role = Role.getFromId(role_id)
    if not target_role:
        return "A role with that id was not found on the server.", 404

    if not user.overseesUser(target_user) and user != target_user:
        return "You do not have permission to assign roles to this user.", 403
    if not user.overseesRole(target_role):
        return "You do not have permission to assign this role.", 403

    target_user.addRole(target_role)
    app.db.session.commit()

    return flask.redirect("/users/" + str(user_id) + "/", code=303)


@app.app.route("/api/users/<int:user_id>/roles/<int:role_id>/", methods=["DELETE"])
def api_user_delete_role(user_id, role_id):
    data = app.get_data()

    user = users.User.getFromRequestOrAbort()
    if not user.hasPermission(Permission.AssignRoles):
        return "You do not have permission to assign roles.", 403

    target_user = users.User.getFromId(user_id)
    if not target_user:
        return "A user with that id was not found on the server.", 404

    target_role = Role.getFromId(role_id)
    if not target_role:
        return "A role with that id was not found on the server.", 404

    if not user.overseesUser(target_user) and user != target_user:
        return "You do not have permission to assign roles to this user.", 403
    if not user.overseesRole(target_role):
        return "You do not have permission to assign this role.", 403

    target_user.removeRole(target_role)
    app.db.session.commit()

    return flask.redirect("/users/" + str(user_id) + "/", code=303)


# Pages
@app.app.route("/roles/")
def page_view_roles():
    return flask.render_template(
        "roles/index.html",
        user=users.User.getFromRequest(),
        Permission=Permission,
        root_role=Role.getRootRole(),
    )


@app.app.route("/roles/<int:id>/")
def page_view_role(id):
    role = Role.getFromId(id)

    if not role:
        return flask.render_template(
            "error.html",
            name="Not Found",
            code=404,
            description="This role was not found on the server.",
            show_home=True,
        )

    return flask.render_template(
        "roles/profile.html",
        role=role,
        parent_role=role.getParentRole(),
    )


@app.app.route("/roles/new/")
def page_create_role():
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(Permission.ManageRoles)

    return flask.render_template(
        "roles/new.html",
        user=user,
        roles=app.db.session.execute(app.db.select(Role)).scalars(),
        permissions=Permission,
    )
