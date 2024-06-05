import project.core.app as app
import project.core.utils as utils
import project.core.errors as errors
import project.modules.search as search
import project.modules.users as users
import project.modules.roles as roles
import flask
import sqlalchemy.orm as orm
from datetime import datetime
import icalendar
import re
import uuid


# TODO: Remove this link: https://icalendar.readthedocs.io/en/latest/usage.html#example


class Event(app.db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uid: orm.Mapped[int] = orm.mapped_column(unique=True)
    sequence: orm.Mapped[int] = orm.mapped_column(default=0)
    creator_id: orm.Mapped[int] = orm.mapped_column()
    creation_date: orm.Mapped[str] = orm.mapped_column()
    start_date: orm.Mapped[str] = orm.mapped_column()
    end_date: orm.Mapped[str] = orm.mapped_column()
    title: orm.Mapped[str] = orm.mapped_column()
    description: orm.Mapped[str] = orm.mapped_column(nullable=True)
    location: orm.Mapped[str] = orm.mapped_column(nullable=True)
    attendees: orm.Mapped[str] = orm.mapped_column(default="[]")
    priority: orm.Mapped[int] = orm.mapped_column(default=0)

    # TODO: Thoroughly check time zone formats

    def getAll():
        return app.db.session.execute(app.db.select(Event)).scalars()

    def getFromId(id: int):
        return app.db.session.execute(
            app.db.select(Event).where(Event.id == id)
        ).scalar_one_or_none()

    def generateCalendar():
        calendar = icalendar.Calendar()

        calendar.add("prodid", "-//Apple Pi Robotics//applepirobotics.org//EN")
        calendar.add("version", "2.0")

        for event in Event.getAll().fetchall():
            calendar.add_component(event.generateEvent())

        return calendar.to_ical().decode("utf-8").replace("\r\n", "\n").strip()

    def generateEvent(self):
        event = icalendar.Event()

        event.add("uid", self.uid)
        event.add("summary", self.title)
        event.add("description", self.description)
        event.add("location", self.location)
        event.add("url", flask.request.host_url + "/events/%d/" % self.id)

        # TODO: STATUS, TRANSP, RRULE, CATEGORIES, GEO, URL

        # TODO: Alarms (reminders)
        # reminder = icalendar.Alarm()
        # reminder.add('action', 'DISPLAY')
        # reminder.add('trigger', timedelta(hours=-1))
        # reminder.add('description', 'Reminder: Event in 1 hour')
        # event.add(reminder)

        # TODO: Event reoccurrence

        event.add("dtstamp", utils.now())
        event.add("created", datetime.fromisoformat(self.creation_date))
        event.add("dtstart", datetime.fromisoformat(self.start_date))
        event.add("dtend", datetime.fromisoformat(self.end_date))

        # TODO: Add organizer and attendees
        # for attendee_id in json.loads(self.attendees):
        #     event.add(
        #         "attendee",
        #     )

        return event


search.SearchEngine(
    Event,
    [
        {
            "value": "title",
            "method": search.basic_text,
            "multiplier": 2.0,
        },
        {
            "value": "description",
            "method": search.basic_text,
            "multiplier": 1.0,
        },
        {
            "value": "start_date",
            "method": search.time_iso,
            "multiplier": 1.5,
        },
        {
            "value": "end_date",
            "method": search.time_iso,
            "multiplier": 1.5,
        },
        {
            "value": "creation_date",
            "method": search.time_iso,
            "multiplier": 1.5,
        },
    ],
    {
        "type": "Event",
        "name": lambda self: self.title,
        "url": lambda self: "/events/" + str(self.id) + "/",
    },
)


# API
@app.app.route("/api/events/", methods=["POST"])
@app.app.route("/api/events/<int:id>/", methods=["PUT", "DELETE"])
def api_create_event(id=None):
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(roles.Permission.EditEvents)

    data = app.get_data()

    event = None
    if flask.request.method == "POST":
        event = Event()
        event.uid = str(uuid.uuid4())
        event.creation_date = utils.now_iso()
        event.start_date = data["starting"] + ":00.000000+00:00"  # TODO: Check time
        event.end_date = data["ending"] + ":00.000000+00:00"
    else:
        event = Event.getFromId(id)
    if flask.request.method == "DELETE":
        app.db.session.delete(event)
        app.db.session.commit()
        return flask.redirect("/events/")

    # TODO: Validate/require options

    event.creator_id = user.id
    event.title = data["title"]
    event.description = data["description"]

    app.db.session.add(event)
    app.db.session.commit()

    return flask.redirect(
        "/events/%d/" % event.id
    )  # TODO: Make all redirects like this


# Pages
@app.app.route("/events/calendar.ics/")
def pages_events_calendar():
    calendar = Event.generateCalendar()
    response = flask.Response(calendar)
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    response.mimetype = "text/calendar .ics"
    return response


@app.app.route("/events/")
def pages_events():
    user = users.User.getFromRequest()

    return flask.render_template(
        "/events/index.html",
        events=Event.getAll(),
        allow_new=user and user.hasPermission(roles.Permission.EditEvents),
        ical_url=re.findall(".*:\/\/(.*?)\/", flask.request.host_url)[0],
    )


@app.app.route("/events/calendar/")
def pages_event_calendar():
    user = users.User.getFromRequest()

    return flask.render_template(
        "/events/calendar.html",
        events=Event.getAll(),
        allow_new=user and user.hasPermission(roles.Permission.EditEvents),
    )


@app.app.route("/events/new/")
def pages_create_event():
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(roles.Permission.EditEvents)

    return flask.render_template(
        "/events/new.html",
    )


@app.app.route("/events/<int:id>/edit/")
def pages_edit_event(id: int):
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(roles.Permission.EditEvents)

    event = Event.getFromId(id)
    if not event:
        raise errors.InstanceNotFound

    return flask.render_template("/events/edit.html", event=event)


@app.app.route("/events/<int:id>/")
def pages_view_event(id):
    user = users.User.getFromRequest()

    event = app.db.session.execute(
        app.db.select(Event).where(Event.id == id)
    ).scalar_one_or_none()

    if not event:
        raise errors.InstanceNotFound

    return flask.render_template(
        "/events/profile.html",
        event=event,
        can_edit=user.hasPermission(roles.Permission.EditEvents),
    )
