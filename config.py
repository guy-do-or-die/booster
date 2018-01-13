DEBUG = False

SLEEP_AFTER_LOGIN = 2
SLEEP_ON_ERROR = 15

LOAD_TIMEOUT = 120

DB = ''

LOG_FORMAT = '%(asctime)-15s %(message)s'


# hush!

import secrets

GUYS = secrets.GUYS
API_KEY = secrets.API_KEY
SITE_KEY = secrets.SITE_KEY

LOGIN_URL = secrets.LOGIN_URL
SURF_URL = secrets.SURF_URL

PASSWORD = getattr(secrets, 'PASSWORD')
