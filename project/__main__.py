from os import system
from sys import path

system("clear")

path.append(".")
path.append("../")

from project.core import app, pages, errors, utils
import project.templates
from project.modules import users, roles, articles, posts, manage, media

app.run()
