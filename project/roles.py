from app import (
    app,
    db,
    Mapped,
    mapped_column,
    render_template,
    on_create_all,
    getenv,
    request,
    make_response,
    redirect,
    get_data,
)

from enum import Enum
from json import dumps, loads
from datetime import datetime
import users
from utils import timestamp

Permission = Enum(
    "Permission",
    [
        "ManageRoles",
        "AssignRoles",
        "PreviewDocuments",
        "EditDocuments",
        "EditMedia",
    ],
)


class Role(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(nullable=True)
    creation_date: Mapped[float] = mapped_column()
    label: Mapped[str] = mapped_column(unique=True)
    permissions: Mapped[str] = mapped_column(default="[]")
    description: Mapped[str] = mapped_column(nullable=True)

    def getFromId(id: int):
        return db.session.execute(
            db.select(Role).where(Role.id == id)
        ).scalar_one_or_none()

    def getRootRole():
        return Role.getFromId(1)

    def getUsers(self):
        all_users = []
        for user in db.session.execute(db.select(users.User)).scalars():
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
        return db.session.execute(
            db.select(Role).where(Role.parent_id == self.id)
        ).scalars()

    def getPermissions(self):
        permissions = []
        for permission_name in loads(self.permissions):
            permissions.append(Permission[permission_name])
        return permissions

    def setPermissions(self, permissions):
        # TODO: Remove invalid permissions

        raw_permissions = []
        for permission in permissions:
            raw_permissions.append(permission.name)
        self.permissions = dumps(raw_permissions)

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
@on_create_all
def create_admin():
    if not Role.getRootRole():
        label = Role.formatLabel(getenv("ADMIN_USERNAME"))

        permissions = []
        for permission_item in Permission:
            permissions.append(permission_item.name)

        root_role = Role(
            creation_date=timestamp(),
            label=label,
            permissions=dumps(permissions),
            description="The role reserved for the administrator account.",
        )

        db.session.add(root_role)
        db.session.commit()


# API
@app.route("/api/roles/", methods=["POST"])
def api_create_role():
    user = users.User.getFromRequestOrAbort()
    if not user.hasPermission(Permission.ManageRoles):
        return "You do not have permission to manage roles.", 403

    # TODO: Validate label properly
    # TODO: Validate parent

    data = get_data()

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
        creation_date=timestamp(),
        label=Role.formatLabel(data["label"]),
        permissions=dumps(permissions),
        description=data["description"],
    )

    db.session.add(role)
    db.session.commit()

    return redirect("/roles/" + str(role.id) + "/")


@app.route("/api/users/<int:user_id>/roles/", methods=["PATCH"])
def api_user_patch_role(user_id):
    data = get_data()

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
    db.session.commit()

    return redirect("/users/" + str(user_id) + "/", code=303)


@app.route("/api/users/<int:user_id>/roles/<int:role_id>/", methods=["DELETE"])
def api_user_delete_role(user_id, role_id):
    data = get_data()

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
    db.session.commit()

    return redirect("/users/" + str(user_id) + "/", code=303)


# Pages
@app.route("/roles/")
def page_view_roles():
    return render_template(
        "roles/index.html",
        user=users.User.getFromRequest(),
        Permission=Permission,
        root_role=Role.getRootRole(),
    )


@app.route("/roles/<int:id>/")
def page_view_role(id):
    role = Role.getFromId(id)

    if not role:
        return render_template(
            "error.html",
            name="Not Found",
            code=404,
            description="This role was not found on the server.",
            show_home=True,
        )

    return render_template(
        "roles/profile.html",
        role=role,
        parent_role=role.getParentRole(),
    )


@app.route("/roles/new/")
def page_create_role():
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(Permission.ManageRoles)

    return render_template(
        "roles/new.html",
        user=user,
        roles=db.session.execute(db.select(Role)).scalars(),
        permissions=Permission,
    )
