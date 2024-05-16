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
        ("About Us", "/about-us/"),
        ("Posts", "/posts/"),
        ("Our Team", "/team/"),
        user_button,
    ]

    result = """<header>
        <div class='background'></div>
        <div class='content'>
            <h1>Apple Pi Robotics</h1>
            <nav>
                <a href="/"><image src="/resources/images/favicon.ico"></image></a>"""
    
    for page in pages:
        if flask.request.path == page[1]: # Is this button for the current page?
            result += """<a href='%s'>
                <div>
                    <b>%s</b>
                </div>
            </a>""" % (page[1], page[0])
        else:
            result += """<a href='%s'>
                <div>%s</div>
            </a>""" % (page[1], page[0])
    
    result += """
            </nav>
        </div>
    </header>"""

    return {"header": result}
