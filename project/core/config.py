import os.path as path
import json

config_exists = path.isfile("config.json")

if not config_exists:
    file = open("config.json", "a+")
    file.write(
        """{
\t"MODE": "dev",
\t"ADMIN_USERNAME": "admin",
\t"ADMIN_PASSWORD": "admin",
\t"PROD_HOST": "127.0.0.1",
\t"PROD_PORT": 8080,
\t"PROD_PROXY": false
}"""
    )
    print("Please modify the new config.json file and run when ready.")
    file.close()
    exit()

file = open("config.json", "r")
CONFIG = json.loads(file.read())
file.close()

def get_config(key):
    if not key in CONFIG:
        return None
    return CONFIG[key]