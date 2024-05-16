import project.core.app as app

result = """<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
<link rel="icon" type="image/x-icon" href="/resources/images/favicon.ico/">
<link rel="stylesheet" href="/resources/css/styles.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
"""

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
