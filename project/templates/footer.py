import project.core.app as app
import project.core.utils as utils
import flask

contact_email = "applepirobotics4H@gmail.com"


@app.add_template
def footer():
    year = utils.now().year

    return {
        "footer": """
<footer>
    <hr>
    <div class='background'></div>
    <div class='content center'>
        <address>
            <p>
                <label>Contact:</label>
                <a href='mailto:%s'>%s</a>    
            </p>
            <p>
            <label>Social Media:</label>
            <a href='https://www.facebook.com/people/Apple-Pi-Robotics-FRC-Team-2067/100054299360253/'>Facebook</a> |
            <a href='https://www.twitter.com/FRC2067'>Twitter</a>
            </p>
            <p>
                <label>Address:</label>
                29 Soundview Rd.
                Building 2, Unit #3
                Guilford, CT 06437
            </p>
        </address>
        <p>© %s Apple Pi Robotics</p>
    </div>
</footer>
"""
        % (contact_email, contact_email, year)
    }
