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
)

from enum import Enum
from json import dumps, loads
from datetime import datetime
from users import User
from utils import timestamp

Permission = Enum(
    "Permission",
    [
        "ManageRoles",
        "AssignRoles",
        "PreviewDocuments",
        "EditDocuments",
    ],
)


class Role(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(nullable=True)
    label: Mapped[str] = mapped_column()
    creation_date: Mapped[float] = mapped_column()
    permissions: Mapped[str] = mapped_column(default="[]")
    description: Mapped[str] = mapped_column(nullable=True)

    def getFromId(id: int):
        return db.session.execute(
            db.select(Role).where(Role.id == id)
        ).scalar_one_or_none()

    def getRootRole():
        return Role.getFromId(1)

    def getParentRole(self):
        if self.parent_id == None:
            return

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
        return db.session.execute(db.select(Role).where(Role.parent_id == self.id)).scalars()

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
    user = User.getFromRequest()
    if not user:
        return "You must be logged in to create a role.", 401

    # TODO: Validate label properly
    # TODO: Validate parent

    data = request.get_json(force=True)

    parent = Role.getFromId(int(data["parent"]))
    if not parent:
        return "The parent supplied does not exist.", 404

    permissions = []
    for permission in Permission:
        if not "permission-" + permission.name in data:
            continue
        # TODO: Validate permissions
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


# Pages
@app.route("/roles/")
def page_view_roles():    
    return render_template("roles/index.html", root_role=Role.getRootRole())


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
        "roles/profile.html", role=role, parent_role=role.getParentRole()
    )


@app.route("/roles/new/")
def page_create_role():
    # TODO: (in roles/new.html) only show valid permissions and roles
    return render_template(
        "roles/new.html",
        roles=db.session.execute(db.select(Role)).scalars(),
        permissions=Permission,
    )
