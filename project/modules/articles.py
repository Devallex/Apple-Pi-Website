import project.core.app as app
import project.core.utils as utils
import project.modules.users as users
import project.modules.roles as roles
import project.modules.search as search
import sqlalchemy.orm as orm
import project.core.errors as errors
import flask
from datetime import datetime


class Article(app.db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    creation_date: orm.Mapped[str] = orm.mapped_column()
    creator_id: orm.Mapped[int] = orm.mapped_column()
    is_published: orm.Mapped[bool] = orm.mapped_column(default=False)
    path: orm.Mapped[str] = orm.mapped_column(unique=True, nullable=True)
    title: orm.Mapped[str] = orm.mapped_column(unique=True)
    abstract: orm.Mapped[str] = orm.mapped_column(nullable=True)
    body: orm.Mapped[str] = orm.mapped_column()
    # history: orm.Mapped[str] = orm.mapped_column(nullable=True) # TODO: History

    def getCreator(self):
        return users.User.getFromId(self.creator_id)

    def getFromId(id):
        return app.db.session.execute(
            app.db.select(Article).where(Article.id == id)
        ).scalar_one_or_none()


search.SearchEngine(
    Article,
    [
        {
            "value": "title",
            "method": search.basic_text,
            "multiplier": 2.0,
        },
        {
            "value": "path",
            "method": search.basic_text,
            "multiplier": 1.5,
        },
        {
            "value": "abstract",
            "method": search.basic_text,
            "multiplier": 1.5,
        },
        {
            "value": "body",
            "method": search.formatted_text,
            "multiplier": 1.0,
        },
        {
            "value": "creation_date",
            "method": search.time_iso,
            "multiplier": 1.0,
        },
    ],
    {
        "type": "Article",
        "name": lambda self: self.title,
        "url": lambda self: (self.path and "/" + self.path + "/")
        or ("/articles/" + str(self.id) + "/"),
    },
)


# API
@app.app.route("/api/articles/", methods=["POST"])
@app.app.route("/api/articles/<int:id>/", methods=["PUT", "DELETE"])
def api_create_article(id: int = None):
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(roles.Permission.EditArticles)

    article = None
    if flask.request.method == "POST":
        article = Article()
        article.creation_date = utils.now_iso()
    else:
        article = Article.getFromId(id)
    if flask.request.method == "DELETE":
        app.db.session.delete(article)
        app.db.session.commit()
        return flask.redirect("/articles/")

    data = app.get_data()

    if "title" in data and len(data["title"]) > 30:
        return "Title cannot exceed 30 characters!"
    if "path" in data and len(data["path"]) > 100:
        return "URL cannot exceed 100 characters!"
    if "body" in data and len(data["body"]) > 10000:
        return (
            "Body cannot exceed 10000 characters! Please remove at least %d."
            % len(data["body"])
            - 10000
        )

    # TODO: Validate path, ensure unique
    path = data["path"] or None
    if path:
        while "//" in path:
            path.replace("//", "/")
        path = path.lower().removeprefix("/").removesuffix("/")

    article.creator_id = user.id
    article.is_published = "is_published" in data
    article.title = data["title"]
    article.body = data["body"]
    article.path = path

    app.db.session.add(article)
    app.db.session.commit()

    return flask.redirect("/articles/" + str(article.id) + "/")


# Pages
@app.app.route("/articles/new/")
def page_create_article():
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(roles.Permission.EditArticles)

    return flask.render_template(
        "/articles/new.html",
    )


@app.app.route("/articles/<int:id>/edit/")
def page_edit_article(id: int):
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(roles.Permission.EditPosts)

    article = Article.getFromId(id)
    if not article:
        raise errors.InstanceNotFound

    return flask.render_template(
        "/articles/edit.html",
        article=article,
    )


@app.app.route("/articles/")
def page_view_articles():
    user = users.User.getFromRequest()

    articles = (
        app.db.session.execute(
            app.db.select(Article).order_by(Article.creation_date.desc())
        )
        .scalars()
        .fetchmany(25)
    )
    user = users.User.getFromRequest()

    items = []
    for article in articles:
        if not article.is_published:
            if not user:
                continue
            if not (
                user.hasAPermission(
                    roles.Permission.EditArticles, roles.Permission.PreviewArticles
                )
            ):
                continue

        items.append(
            {
                "id": article.id,
                "creation_date": article.creation_date,
                "creator": users.User.getFromId(article.creator_id).getNameText(),
                "title": article.title,
                "abstract": article.abstract,
                "body": article.body,
            }
        )

        if len(items) >= 25:
            break

    return flask.render_template(
        "/articles/index.html",
        title="Articles",
        base_url="/articles/",
        max_abstract=250,
        items=items,
        allow_new=user and user.hasPermission(roles.Permission.EditArticles),
    )


@app.app.route("/articles/<int:id>/")
def page_view_article(id):
    article = app.db.session.execute(
        app.db.select(Article).where(Article.id == id)
    ).scalar_one_or_none()

    if not article:
        raise errors.InstanceNotFound

    if not article.is_published:
        user = users.User.getFromRequestOrAbort()
        user.hasAPermissionOrAbort(
            roles.Permission.PreviewArticles, roles.Permission.EditArticles
        )

    user = users.User.getFromRequest()

    creator = users.User.getFromId(article.creator_id)

    return flask.render_template(
        "/articles/profile.html",
        title=article.title,
        document_type="Article",
        creator=creator,
        creation_date=datetime.fromisoformat(article.creation_date),
        is_published=article.is_published,
        body=article.body,
        path=article.path,
        id=article.id,
        can_edit=user and user.hasAPermission(roles.Permission.EditArticles),
    )
