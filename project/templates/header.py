import project.core.app as app
import project.modules.users as users
import flask


@app.add_template
def header():
    user = users.User.getFromRequest()

    user_button = ("Log In", "/login/")
    if user:
        user_button = ("Manage: <b>" + user.getDisplayName() + "</b>", "/manage/")

    pages = [
        ("Home", "/"),
        ("About Us", "/about-us/"),
        ("Posts", "/posts/"),
        ("Our Team", "/team/"),
        user_button,
    ]

    result = """<header><div class='background'></div><div class='content'>"""

    for page in pages:
        if flask.request.path == page[1]:
            result += "\n\t<a href='%s'><div><b>%s</b></div></a>" % (page[1], page[0])
        else:
            result += "\n\t<a href='%s'><div>%s</div></a>" % (page[1], page[0])
    result += "</div></header>"

    return {"header": result}
