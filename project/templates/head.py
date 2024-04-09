import project.core.app as app

result = """<link rel="stylesheet" href="/resources/css/styles.css">
<link rel="icon" type="image/x-icon" href="/favicon.ico/">"""

scripts = (
    "globals",
    "api",
    "cookies",
    "users",
    "editor",
    # "header",
    # "footer",
)
for script in scripts:
    result += "\n	<script src='/resources/js/%s.js' defer></script>" % script


@app.add_template
def header():
    return {"head": result}
