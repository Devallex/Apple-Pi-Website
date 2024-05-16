import project.core.app as app
import flask


@app.add_template
def breadcrumbs():
    result = ("""
        <span class='breadcrumbs'>
            <span class='background'></span>
            <span class='content'>
                <a href='/'>home</a>
    """)

    sub_paths = (
        flask.request.path.lower().removeprefix("/").removesuffix("/").split("/")
    )

    current_path = "/"
    for sub_path in sub_paths:
        if not sub_path:
            continue

        current_path += sub_path + "/"
        # TODO: Use the HTML document's title instead of the sub_path
        result += " / "
        if sub_path == sub_paths[-1]:
            result += "<b>%s</b>" % sub_path
        else:
            result += "<a href='%s'>%s</a>" % (current_path, sub_path)

    result += """
            </span>
        </span>
    """
    
    return {"breadcrumbs": result}
