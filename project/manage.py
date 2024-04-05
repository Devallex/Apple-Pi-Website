from app import app, render_template
from users import User


@app.route("/manage/")
def page_manage():
    user = User.getFromRequestOrAbort()

    
    return render_template("manage.html", user=user)