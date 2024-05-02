import project.core.app as app
import project.core.errors as errors
import project.modules.users as users
import project.modules.roles as roles
import sqlalchemy.orm as orm
from datetime import datetime
import flask
import urllib.parse as parse
from project.core.utils import time, timestamp


class Post(app.db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    creation_date: orm.Mapped[float] = orm.mapped_column()
    creator_id: orm.Mapped[int] = orm.mapped_column()
    is_published: orm.Mapped[str] = orm.mapped_column(default=False)
    event: orm.Mapped[int] = orm.mapped_column(nullable=True)
    propagate: orm.Mapped[bool] = orm.mapped_column(default=False)
    title: orm.Mapped[str] = orm.mapped_column(unique=True)
    abstract: orm.Mapped[str] = orm.mapped_column(nullable=True)
    body: orm.Mapped[str] = orm.mapped_column()
    # history: orm.Mapped[str] = orm.mapped_column(nullable=True) # TODO: History

    def getCreator(self):
        return users.User.getFromId(self.creator_id)

    def getDateText(self):
        return str(datetime.fromtimestamp(self.creation_date))


# API
@app.app.route("/api/posts/", methods=["POST"])
def api_create_post():
    data = app.get_data()

    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(roles.Permission.EditPosts)

    title = data["title"]
    existing_post = app.db.session.execute(
        app.db.select(Post).where(Post.title == title)
    ).scalar_one_or_none()

    if existing_post:
        return (
            "This title is already taken by another post. Please choose another one.",
            403,
        )

    post = Post(
        creation_date=timestamp(),
        creator_id=user.id,
        is_published="is_published" in data,
        title=title,
        body=data["body"],
    )

    app.db.session.add(post)
    app.db.session.commit()

    return flask.redirect("/posts/" + str(post.id) + "/")


# Feed
@app.app.route("/feed.rss/")
def feed_rss():
    parsed_url = parse.urlparse(flask.request.base_url)
    base_url = parse.urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path.split("/")[0],
            "",
            "",
            "",
        )
    )

    return flask.render_template(
        "feeds/feed.rss",
        base_url=base_url,
        posts=app.db.session.execute(app.db.select(Post)).scalars(),
        max_abstract=250,
        year=time().year,
    )


# Pages
@app.app.route("/posts/new/")
def page_create_post():
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(roles.Permission.EditPosts)

    return flask.render_template(
        "editor.html", document_type="Post", api_url="/posts/", method="post"
    )


@app.app.route("/posts/")
def page_view_posts():
    posts = (
        app.db.session.execute(app.db.select(Post).order_by(Post.creation_date.desc()))
        .scalars()
        .fetchmany(25)
    )
    user = users.User.getFromRequest()

    items = []
    for post in posts:
        if not post.is_published:
            if not user:
                continue
            if not (
                user.hasAPermission(
                    roles.Permission.EditPosts, roles.Permission.PreviewPosts
                )
            ):
                continue

        items.append(
            {
                "id": post.id,
                "creation_date": post.getDateText(),
                "creator": users.User.getFromId(post.creator_id).getNameText(),
                "title": post.title,
                "body": post.body,
            }
        )

        if len(items) >= 25:
            break

    return flask.render_template(
        "library.html",
        title="Posts",
        base_url="/posts/",
        max_abstract=250,
        items=items,
        allow_new=user and user.hasPermission(roles.Permission.EditPosts),
    )


@app.app.route("/posts/<int:id>/")
def page_view_post(id):
    post = app.db.session.execute(
        app.db.select(Post).where(Post.id == id)
    ).scalar_one_or_none()

    if not post:
        raise errors.InstanceNotFound

    creator = users.User.getFromId(post.creator_id)

    return flask.render_template(
        "document.html",
        title=post.title,
        document_type="Post",
        creator=creator,
        creation_date=post.getDateText(),
        body=post.body,
    )
