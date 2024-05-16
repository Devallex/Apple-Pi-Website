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
        ("Home", "/", "navbar-only"),
        ("About Us", "/about-us/"),
        ("Events", "/events/"),
        ("Posts", "/posts/"),
        ("Media", "/media/"),
        ("Our Team", "/team/"),
        user_button,
    ]

    result = """
<header>
    <script>
        function openNav() {
            document.getElementById("myNav").style.display = "block";
        }

        function closeNav() {
            document.getElementById("myNav").style.display = "none";
        }
    </script>
    
    <div class="navbar">
        <a href="/">
            <img id="logo" src="/resources/images/banner.png">
        </a>
        <ul id="navlist">
            %s
            <span id="hamb" style="font-size:30px;cursor:pointer;padding-top: 10px;" onclick="openNav()">&#9776;</span>
        </ul>
    </div>

    <div id="myNav" class="overlay">
        <a href="javascript:void(0)" class="closebtn" onclick="closeNav()">&times;</a>
        <div class="overlay-content">
            %s
        </div>
    </div>
</header>
"""

    navbar_links = ""
    overlay_links = ""

    for page in pages:
        page_link = ""
        if flask.request.path == page[1]:  # Is this button for the current page?
            page_link = """<a href='%s'><div><b>%s</b></div></a>""" % (
                page[1],
                page[0],
            )
        else:
            page_link = """<a href='%s'><div>%s</div></a>""" % (
                page[1],
                page[0],
            )
        if not "navbar-only" in page:
            navbar_links += "<li>" + page_link + "</li>"
        overlay_links += page_link

    result = result % (navbar_links, overlay_links)

    return {"header": result}
