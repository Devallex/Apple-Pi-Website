from app import app, db, Mapped, mapped_column, request, render_template, redirect
from documents import Document

from users import User
from time import time


class Post(Document):
    event: Mapped[int] = mapped_column(nullable=True)
    propagate: Mapped[bool] = mapped_column(default=False)


# API
@app.route("/api/posts/", methods=["POST"])
def api_create_post():
    data = request.get_json(force=True)

    user = User.getFromRequest()
    if not user:
        return "You must be logged in to create a post.", 401

    title = data["title"]
    existing_post = db.session.execute(
        db.select(Post).where(Post.title == title)
    ).scalar_one_or_none()

    if existing_post:
        return (
            "This title is already taken by another document (post/article). Please choose another one.",
            403,
        )

    post = Post(
        creation_date=int(time()),
        creator_id=user.id,
        title=title,
        body=data["body"],
        is_published=True,
    )

    db.session.add(post)
    db.session.commit()

    return redirect("/posts/" + str(post.id) + "/")


# Pages
@app.route("/posts/new/")
def page_create_post():
    user = User.getFromRequest()
    if not user:
        return render_template(
            "error.html",
            name="Unauthorized",
            code=401,
            description="You must be signed in to create a post. Try <a href='/login'>logging in</a>.",
            show_home=True,
        )

    return render_template(
        "editor.html", document_type="Post", api_url="/posts/", method="post"
    )


@app.route("/posts/")
def page_view_posts():
    posts = Post.query.order_by(Post.creation_date.desc()).limit(25)
    user = User.getFromRequest()

    items = []
    for post in posts:
        if not post.is_published:
            continue

        items.append(
            {
                "id": post.id,
                "creation_date": post.getDateText(),
                "creator": User.getFromId(post.creator_id).getNameText(),
                "title": post.title,
                "body": post.body,
            }
        )

        if len(items) >= 25:
            break

    return render_template(
        "library.html",
        title="Posts",
        base_url="/posts/",
        max_abstract=250,
        items=items,
        allow_new=user != None,
    )


@app.route("/posts/<int:id>/")
def page_view_post(id):
    post = db.session.execute(db.select(Post).where(Post.id == id)).scalar_one_or_none()

    if not post:
        return render_template(
            "error.html",
            name="Not Found",
            code=404,
            description="This post was not found on the server. It may have been deleted or a faulty link. If you want, you can <a href='/posts/>view all the posts here</a>.",
            show_home=True,
        )

    creator = User.getFromId(post.creator_id)

    return render_template(
        "document.html",
        title=post.title,
        document_type="Post",
        creator=creator,
        creation_date=post.getDateText(),
        body=post.body,
    )
