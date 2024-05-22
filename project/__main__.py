from sys import path

path.append(".")
path.append("../")

from project.core import app, pages, errors, utils
import project.templates
from project.modules import users, roles, events, articles, posts, manage, media

app.run()
