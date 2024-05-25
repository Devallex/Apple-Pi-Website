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
    <div class="footer-splitscreen-container">
    <div class="footer-splitscreen-column" id="footer_responsive_stack_first">
        <h2>Contact</h2>
        <p>Email: <a href="mailto:%s">%s</a></p>
        <p>Address: 29 Soundview Rd. Building 2, Unit #3 Guilford, CT 06437</p>
    </div> 
    <div class="footer-splitscreen-column" id="footer_responsive_stack_second">
        <h2>Links</h2>
        <ul>
            <li><a href="/events/">Events</a></li>
            <li><a href="/articles/">Posts</a></li>
            <li><a href="/team/">Our Team</a></li>
        </ul>
    </div>
    <div class="footer-splitscreen-column" id="footer_responsive_stack_third">
        <h2>Socials</h2>
        <a class="fa fa-facebook"
            href="https://www.facebook.com/people/Apple-Pi-Robotics-FRC-Team-2067/100054299360253/"></a>
        <a class="fa fa-twitter" href="https://www.twitter.com/FRC2067"></a>
    </div>
</div>
<p>© %d Apple Pi Robotics</p>
</footer>
"""
        % (contact_email, contact_email, year)
    }
