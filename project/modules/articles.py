import project.core.app as app
import project.modules.users as users
import project.modules.roles as roles
import project.core.utils as utils
import sqlalchemy.orm as orm
import project.core.errors as errors
import flask
from datetime import datetime


class Article(app.db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    creation_date: orm.Mapped[float] = orm.mapped_column()
    creator_id: orm.Mapped[int] = orm.mapped_column()
    is_published: orm.Mapped[bool] = orm.mapped_column(default=False)
    path: orm.Mapped[str] = orm.mapped_column(unique=True, nullable=True)
    title: orm.Mapped[str] = orm.mapped_column(unique=True)
    abstract: orm.Mapped[str] = orm.mapped_column(nullable=True)
    body: orm.Mapped[str] = orm.mapped_column()
    # history: orm.Mapped[str] = orm.mapped_column(nullable=True) # TODO: History

    def getCreator(self):
        return users.User.getFromId(self.creator_id)

    def getDateText(self):
        return str(datetime.fromtimestamp(self.creation_date))


# API
@app.app.route("/api/articles/", methods=["POST"])
def api_create_article():
    data = app.get_data()

    user = users.User.getFromRequestOrAbort()
    if not user.hasPermission(roles.Permission.EditArticles):
        return "You do not have permission to publish documents.", 403

    title = data["title"]
    existing_article = app.db.session.execute(
        app.db.select(Article).where(Article.title == title)
    ).scalar_one_or_none()

    if existing_article:
        return (
            "This title is already taken by another article. Please choose another one.",
            403,
        )

    # TODO: Validate path, ensure unique
    path = data["path"] or None
    if path:
        while "//" in path:
            path.replace("//", "/")
        path = path.lower().removeprefix("/").removesuffix("/")

    article = Article(
        creation_date=utils.timestamp(),
        creator_id=user.id,
        is_published="is_published" in data,
        title=title,
        body=data["body"],
        path=path,
    )

    app.db.session.add(article)
    app.db.session.commit()

    return flask.redirect("/articles/" + str(article.id) + "/")


# Pages
@app.app.route("/articles/new/")
def page_create_article():
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(roles.Permission.EditArticles)

    return flask.render_template(
        "editor.html",
        document_type="Article",
        api_url="/articles/",
        method="post",
        other="""<fieldset>
            <legend>Article</legend>
            <label for='path'><b>Path (Optional):</b> Where should the article be located when published?</label><br>
            <input name='path' id='path' type='text'></input>
        </fieldset>""",
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
                user.hasAPermission(roles.Permission.EditArticles, roles.Permission.PreviewArticles)
            ):
                continue

        items.append(
            {
                "id": article.id,
                "creation_date": article.getDateText(),
                "creator": users.User.getFromId(article.creator_id).getNameText(),
                "title": article.title,
                "abstract": article.abstract,
                "body": article.body,
            }
        )

        if len(items) >= 25:
            break

    return flask.render_template(
        "library.html",
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

    creator = users.User.getFromId(article.creator_id)

    return flask.render_template(
        "document.html",
        title=article.title,
        document_type="Article",
        creator=creator,
        creation_date=article.getDateText(),
        is_published=article.is_published,
        body=article.body,
        path=article.path,
    )
