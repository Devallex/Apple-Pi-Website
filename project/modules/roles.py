import project.core.app as app
import project.core.utils as utils
import project.core.errors as errors
import project.core.config as config
import project.modules.users as users
import project.modules.search as search
import flask
import sqlalchemy.orm as orm
import enum
import json

Permission = enum.Enum(
    "Permission",
    [
        "ManageUsers",
        "ManageRoles",
        "AssignRoles",
        "EditEvents",
        "EditPosts",
        "PreviewPosts",
        "EditArticles",
        "PreviewArticles",
        "EditMedia",
    ],
)


class Role(app.db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    parent_id: orm.Mapped[int] = orm.mapped_column(nullable=True)
    creation_date: orm.Mapped[str] = orm.mapped_column()
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

    def getChildRoles(self) -> list:
        if not self.id:
            return []

        return (
            app.db.session.execute(app.db.select(Role).where(Role.parent_id == self.id))
            .scalars()
            .all()
        )

    def getDescendantRoles(self):
        descendants = []
        for child in self.getChildRoles():
            descendants.append(child)
            descendants.extend(child.getDescendantRoles())
        return descendants

    def getPermissions(self):
        permissions = []
        if self.id == 1:
            for permission in Permission:
                permissions.append(permission)
        else:
            for permission_name in json.loads(self.permissions):
                permissions.append(Permission[permission_name])
        return permissions

    def getStringPermissions(self):
        string_permissions = ""
        for permission in self.getPermissions():
            string_permissions += permission.name + " "
        string_permissions = string_permissions.strip()
        return string_permissions

    def setPermissions(self, permissions):
        # TODO: Remove invalid permissions
        if self.id == 1:
            self.permissions = "[]"

        raw_permissions = []
        for permission in permissions:
            raw_permissions.append(permission.name)
        self.permissions = json.dumps(raw_permissions)

    def hasPermission(self, permission: Permission):
        if self.id == 1:
            return True
        return permission in self.getPermissions()

    def overseesRole(self, role) -> bool:
        parent_role = role
        while parent_role:
            parent_role = parent_role.getParentRole()
            if parent_role == self:
                return True
        return False


search.SearchEngine(
    Role,
    [
        {
            "value": "label",
            "method": search.basic_text,
            "multiplier": 2.0,
        },
        {
            "value": "description",
            "method": search.basic_text,
            "multiplier": 1.0,
        },
        {
            "value": "getStringPermissions",
            "method": search.basic_text,
            "multiplier": 1.0,
        },
        {
            "value": "creation_date",
            "method": search.time_iso,
            "multiplier": 1.0,
        },
    ],
    {
        "type": "Role",
        "name": lambda self: self.label,
        "url": lambda self: "/roles/" + str(self.id) + "/",
    },
)


# Create Admin
@app.on_create_all
def create_admin():
    if not Role.getRootRole():
        label = Role.formatLabel(config.get_config("ADMIN_USERNAME"))

        root_role = Role(
            creation_date=utils.now_iso(),
            label=label,
            description="The role reserved for the administrator account.",
        )

        app.db.session.add(root_role)
        app.db.session.commit()


# API
@app.app.route("/api/roles/", methods=["POST"])
@app.app.route("/api/roles/<int:id>/", methods=["PUT", "DELETE"])
def api_create_role(id=None):
    user = users.User.getFromRequestOrAbort()
    user.hasAPermissionOrAbort(Permission.ManageRoles)

    # TODO: Validate label properly
    # TODO: Validate parent

    role = None
    if flask.request.method == "POST":
        role = Role()
        role.creation_date = utils.now_iso()
    else:
        role = Role.getFromId(id)
        if not user.overseesRole(role):
            raise errors.NeedPermission

    data = app.get_data()
    parent = None
    if "parent" in data:
        parent = Role.getFromId(int(data["parent"]))
    else:
        parent = role.getParentRole()
    if not parent:
        raise errors.InstanceNotFound
    print(user.roles)
    if not user.overseesRole(parent) and not user.hasRole(parent):
        raise errors.exceptions.Forbidden

    if flask.request.method == "DELETE":
        for deleted_role in role.getDescendantRoles() + [role]:
            for user in deleted_role.getUsers():
                user.removeRole(role)
            app.db.session.delete(deleted_role)
        app.db.session.commit()
        return flask.redirect("/roles/")

    permissions = []
    for permission in Permission:
        if not "permission-" + permission.name in data:
            continue
        if not user.hasPermission(permission):
            continue
        if data["permission-" + permission.name] == "on":
            permissions.append(permission.name)

    if parent == role or parent in role.getDescendantRoles():
        return "This is an invalid parent that would cause a recursive dependency loop."

    role.parent_id = parent.id
    role.creation_date = utils.now_iso()
    role.label = Role.formatLabel(data["label"])
    role.permissions = json.dumps(permissions)
    role.description = data["description"]

    app.db.session.add(role)
    app.db.session.commit()

    return flask.redirect("/roles/" + str(role.id) + "/")


@app.app.route("/api/users/<int:user_id>/roles/", methods=["PATCH"])
def api_user_patch_role(user_id):
    data = app.get_data()

    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(Permission.AssignRoles)

    target_user = users.User.getFromId(user_id)
    if not target_user:
        raise errors.InstanceNotFound

    role_id = data["role_id"]
    if not role_id:
        return "Please select a role to add."

    target_role = Role.getFromId(role_id)
    if not target_role:
        raise errors.InstanceNotFound

    if not user.overseesUser(target_user) and user != target_user:
        raise errors.NeedPermission
    if not user.overseesRole(target_role):
        raise errors.NeedPermission

    target_user.addRole(target_role)
    app.db.session.commit()

    return flask.redirect("/users/" + str(user_id) + "/", code=303)


@app.app.route("/api/users/<int:user_id>/roles/<int:role_id>/", methods=["DELETE"])
def api_user_delete_role(user_id, role_id):
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(Permission.AssignRoles)

    target_user = users.User.getFromId(user_id)
    if not target_user:
        raise errors.InstanceNotFound

    target_role = Role.getFromId(role_id)
    if not target_role:
        raise errors.InstanceNotFound

    if not user.overseesUser(target_user) and user != target_user:
        raise errors.NeedPermission
    if not user.overseesRole(target_role):
        raise errors.NeedPermission

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
    user = users.User.getFromRequest()

    if not role:
        raise errors.InstanceNotFound

    return flask.render_template(
        "roles/profile.html",
        user=user,
        role=role,
        parent_role=role.getParentRole(),
        Permission=Permission,
    )


@app.app.route("/roles/new/")
def page_create_role():
    parent_id = flask.request.args.get("parent")
    parent = None
    if parent_id:
        parent = Role.getFromId(parent_id)

    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(Permission.ManageRoles)

    return flask.render_template(
        "/roles/new.html",
        user=user,
        roles=app.db.session.execute(app.db.select(Role)).scalars(),
        parent=parent,
        permissions=Permission,
    )


@app.app.route("/roles/<int:id>/edit/")
def page_edit_role(id):
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(Permission.ManageRoles)

    role = Role.getFromId(id)
    if not user.overseesRole(role):
        raise errors.NeedPermission

    return flask.render_template(
        "/roles/edit.html",
        user=user,
        role=role,
        roles=app.db.session.execute(app.db.select(Role)).scalars(),
        permissions=Permission,
    )
