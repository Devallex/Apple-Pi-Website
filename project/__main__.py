from sys import path

path.append(".")
path.append("../")

from project.core import config, app, pages, errors, utils
import project.templates
from project.modules import users, roles, articles, posts, manage, events

app.run()
