DEBUG = True

PAGES_PER_DAY = 100
SLEEP_ON_ERROR = 15
LOAD_TIMEOUT = 60

LOG_FORMAT = '%(asctime)-15s %(message)s'

THREADS_NUM = 2

TOR_PORT = 9051

DB = {
    'name': 'booster',
    'host': '127.0.0.1',
    'port': 27017
}

# hush!

import secrets

GUYS = secrets.GUYS
API_KEY = secrets.API_KEY
SITE_KEY = secrets.SITE_KEY

LOGIN_URL = secrets.LOGIN_URL
SURF_URL = secrets.SURF_URL
STAT_URL = secrets.STAT_URL

PASSWORD = getattr(secrets, 'PASSWORD')
