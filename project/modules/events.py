import project.core.app as app
import project.core.utils as utils
import project.core.errors as errors
import project.modules.users as users
import project.modules.roles as roles
import flask
import sqlalchemy.orm as orm
from datetime import datetime, timezone, timedelta
import icalendar
import pytz
import json
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


# TODO: Add search engine for events


# API
@app.app.route("/api/events/", methods=["POST"])
def api_create_event():
    user = users.User.getFromRequestOrAbort()
    user.hasPermissionOrAbort(roles.Permission.EditEvents)

    data = app.get_data()

    print(data["starting"])

    # TODO: Validate/require options

    event = Event(
        uid=str(uuid.uuid4()),
        creator_id=user.id,
        creation_date=utils.now_iso(),
        start_date=data["starting"] + ":00.000000+00:00",  # TODO: Check time
        end_date=data["ending"] + ":00.000000+00:00",
        title=data["title"],
        description=data["description"],
    )

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
        user=user,
    )
