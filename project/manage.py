from app import app, render_template
from users import User

@app.route("/manage/")
def page_manage():
    user = User.getFromRequest()
    if not user:
        return render_template(
            "error.html",
            name="Unauthorized",
            code=401,
            description="You must be signed in to access the management panel. Try <a href='/login'>logging in</a>.",
            show_home=True,
        )

    
    return render_template("manage.html", user=user)