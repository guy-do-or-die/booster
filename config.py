DEBUG = True

SLEEP_AFTER_LOGIN = 2
SLEEP_ON_ERROR = 15

LOAD_TIMEOUT = 120

DB = ''

# hush!

import secrets

GUYS = secrets.GUYS
API_KEY = secrets.API_KEY
SITE_KEY = secrets.SITE_KEY

PASSWORD = getattr(secrets, 'PASSWORD')
