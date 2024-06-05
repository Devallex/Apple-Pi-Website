import project.core.app as app

result = """
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
<link rel="icon" type="image/x-icon" href="/resources/images/icon.svg/">
<link rel="stylesheet" href="/resources/css/styles.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
<!-- Quill.js -->
<link href="https://cdn.jsdelivr.net/npm/quill@2.0.1/dist/quill.snow.css" rel="stylesheet" />
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.js" integrity="sha384-hIoBPJpTUs74ddyc4bFZSM1TVlQDA60VBbJS0oA934VSz82sBx1X7kSx2ATBDIyd" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/quill@2.0.1/dist/quill.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.css" integrity="sha384-wcIxkf4k558AjM3Yz3BBFQUbk/zgIYC2R0QpeeYb+TwlBVMrlgLqwRjRtGZiK7ww" crossorigin="anonymous">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/contrib/auto-render.min.js" integrity="sha384-43gviWU0YVjaDtb/GhzOouOXtZMP/7XUzwPTstBeZFe/+rCMvRwr4yROQP43s0Xk" crossorigin="anonymous" onload="renderMathInElement(document.body);"></script>
"""

scripts = ("globals", "api", "cookies", "users", "editor")
for script in scripts:
    result += "\n	<script src='/resources/js/%s.js' defer></script>" % script


@app.add_template
def header():
    return {"head": result}
