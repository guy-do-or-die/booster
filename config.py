DEBUG = False

PAGE_RATES = [160, 100, 250]
SLEEP_ON_ERROR = 15
LOAD_TIMEOUT = 360

LOG_FORMAT = '%(asctime)-15s %(message)s'

THREADS_NUM = 2

DB = {
    'name': 'booster',
    'host': '127.0.0.1',
    'port': 27018
}

PROXY = '127.0.0.1:8118'
TOR_PORT = 9051

# hush!

import secrets

GUYS = secrets.GUYS
API_KEY = secrets.API_KEY
SITE_KEY = secrets.SITE_KEY

URL = secrets.URL
TPO_URL = secrets.URL
SURF_URL = secrets.SURF_URL
STAT_URL = secrets.STAT_URL
LOGIN_URL = secrets.LOGIN_URL
DASHBOARD = secrets.DASHBOARD
POFILE_URL = secrets.PROFILE_URL
PREFERENCE_URL = secrets.PREFERENCE_URL

PASSWORD = getattr(secrets, 'PASSWORD')
