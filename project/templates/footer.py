import project.core.app as app
import flask

contact_email = "applepirobotics4H@gmail.com"


@app.add_template
def footer():
    return {
        "footer": """
<footer><div class='background'></div>\n<div class='content center'>\n\t<address>\n\t\t<p>\n\t\t\t<label>Contact:</label>\n\t\t\t<a href='mailto:%s'>%s</a>\n\t\t</p>\n\t\t<p>\n\t\t\t<label>Social Media:</label>\n\t\t\t<a href='https://www.facebook.com/people/Apple-Pi-Robotics-FRC-Team-2067/100054299360253/'>Facebook</a> |\n\t\t\t<a href='https://www.twitter.com/FRC2067'>Twitter</a>\n\t\t</p>\n\t\t<p>\n\t\t\t<label>Address:</label>\n\t\t\t29 Soundview Rd.\n\t\t\tBuilding 2, Unit #3\n\t\t\tGuilford, CT 06437\n\t\t</p>\n\t</address>\n</div></footer>
"""
        % (contact_email, contact_email)
    }
