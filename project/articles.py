from app import app, db, Mapped, mapped_column, request, render_template, redirect
from users import User
from roles import Permission
from datetime import datetime
from utils import timestamp


class Article(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    creation_date: Mapped[float] = mapped_column()
    creator_id: Mapped[int] = mapped_column()
    is_published: Mapped[str] = mapped_column(default=False)
    title: Mapped[str] = mapped_column(unique=True)
    abstract: Mapped[str] = mapped_column(nullable=True)
    body: Mapped[str] = mapped_column()
    # history: Mapped[str] = mapped_column(nullable=True) # TODO: History

    def getCreator(self):
        return User.getFromId(self.creator_id)

    def getDateText(self):
        return str(datetime.fromtimestamp(self.creation_date))


# API
@app.route("/api/articles/", methods=["POST"])
def api_create_article():
    data = request.get_json(force=True)

    user = User.getFromRequest()
    if not user:
        return "You must be logged in to create an article.", 401
    if not user.hasPermission(Permission.EditDocuments):
        return "You do not have permission to publish documents.", 403

    title = data["title"]
    existing_article = db.session.execute(
        db.select(Article).where(Article.title == title)
    ).scalar_one_or_none()

    if existing_article:
        return (
            "This title is already taken by another article. Please choose another one.",
            403,
        )

    article = Article(
        creation_date=timestamp(),
        creator_id=user.id,
        title=title,
        body=data["body"],
        is_published=True,
    )

    db.session.add(article)
    db.session.commit()

    return redirect("/articles/" + str(article.id) + "/")


# Pages
@app.route("/articles/new/")
def page_create_article():
    user = User.getFromRequest()
    if not user:
        return render_template(
            "error.html",
            name="Unauthorized",
            code=401,
            description="You must be signed in to create an article. Try <a href='/login'>logging in</a>.",
            show_home=True,
        )
    if not user.hasPermission(Permission.EditDocuments):
        return render_template(
            "error.html",
            name="Forbidden",
            code=403,
            description="You do not have permission to publish documents. If you need to, please ask someone with permission to give you access.",
            show_home=True,
        )

    return render_template(
        "editor.html", document_type="Article", api_url="/articles/", method="post"
    )


@app.route("/articles/")
def page_view_articles():
    articles = (
        db.session.execute(db.select(Article).order_by(Article.creation_date.desc()))
        .scalars()
        .fetchmany(25)
    )
    user = User.getFromRequest()

    items = []
    for article in articles:
        if not article.is_published:
            continue

        items.append(
            {
                "id": article.id,
                "creation_date": article.getDateText(),
                "creator": User.getFromId(article.creator_id).getNameText(),
                "title": article.title,
                "body": article.body,
            }
        )

        if len(items) >= 25:
            break

    return render_template(
        "library.html",
        title="Articles",
        base_url="/articles/",
        max_abstract=250,
        items=items,
        allow_new=user and user.hasPermission(Permission.EditDocuments),
    )


@app.route("/articles/<int:id>/")
def page_view_article(id):
    article = db.session.execute(
        db.select(Article).where(Article.id == id)
    ).scalar_one_or_none()

    if not article:
        return render_template(
            "error.html",
            name="Not Found",
            code=404,
            description="This article was not found on the server. It may have been deleted or a faulty link. If you want, you can <a href='/articles/>view all the articles here</a>.",
            show_home=True,
        )

    creator = User.getFromId(article.creator_id)

    return render_template(
        "document.html",
        title=article.title,
        document_type="Article",
        creator=creator,
        creation_date=article.getDateText(),
        body=article.body,
    )
