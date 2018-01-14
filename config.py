DEBUG = True

SLEEP_ON_ERROR = 15
LOAD_TIMEOUT = 60

DB = ''

LOG_FORMAT = '%(asctime)-15s %(message)s'

THREADS_NUM = 1


# hush!

import secrets

GUYS = secrets.GUYS
API_KEY = secrets.API_KEY
SITE_KEY = secrets.SITE_KEY

LOGIN_URL = secrets.LOGIN_URL
SURF_URL = secrets.SURF_URL

PASSWORD = getattr(secrets, 'PASSWORD')
