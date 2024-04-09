# Overview
These instructions show only Linux/MacOS. Windows is probably supported but commands may be slightly different.
# Development
## Setup
1. [Install Python](https://www.python.org/downloads/)
2. Install Python dependencies:<br>`pip3 install -r requirements.txt`
3. Create `.env` file (Configure options here)
```env
DEBUG=false
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="&DM1N"
```
## Running
1. Start the web server:<br>
`python3 project`
2. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) to preview the project.
# Deployment
1. Download wheel:<br>
`pip3 install build`
2. Build the project:<br>
`python3 -m build --wheel`
3. Setup a virtualenv:
	1. Create a new venv:<br>
	`python3 -m venv .venv`
	2. Activate the new venv:<br>
	`. .venv/bin/activate`
4. Install flaskr:<br>
`pip3 install flaskr-1.0.01-py3-none-any.whl`
5. Configure the secret key:<br>
	1. Create a random key:<br>
	`python3 -c 'import secrets; print(secrets.token_hex())`
	2. Save it to the file (*please fill in **KEY HERE***):<br>
	`echo "SECRET_KEY = 'KEY_HERE'" > config.py`
6. Install waitress:<br>
`pip3 install waitress`
7. Run the server:<br>
`waitress-serve --call 'flaskr:create_app'`
# About
## Directory Structure
A brief overview of each directory in the repository.
> `instance` — A directory containing all the data from the website
>
> `project` — All the files from the site
> > `core` — Scripts which contain a groundwork for the website
> >
> > `modules` — Primary website features (users, articles, media, etc.)
> >
> > `templates` — Scripts which add global variables to jinja templates
> >
> > `website` — Static and dynamic web files
> > > `static` — Web files which can be directly accessed