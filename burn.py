#! .env/bin/python

import ipdb
import time
import http
import socket
import signal
import select
import getpass
import logging

from datetime import datetime

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import config


universal_password = None
solved_captchas = 0


def now():
    return datetime.now().strftime('%Y.%m.%d %H:%M:%S')


logging.basicConfig(filename='logs/{}.log'.format(now()),
                    format=config.LOG_FORMAT,
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)


def log(message, **kwargs):
    guy = kwargs.get('guy')
    type = kwargs.get('type', 'info')

    message = '{}{}'.format(
    message, ' ({}, {})'.format(guy.name, guy.id) if guy else '')

    print('{}: {}'.format(now(), message))
    getattr(logger, type)(message, extra=kwargs)

    if config.DEBUG and type == 'error':
        driver = kwargs.get('driver')
        ipdb.set_trace()


def surf_url(guy):
    return config.SURF_URL.format(guy.id)


def solve_captcha(url, driver):
    driver.switch_to_default_content()
    driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, "iframe[src*='captcha']"))
    driver.find_element_by_id('verify-me').click()
    driver.switch_to_default_content()

    if driver.find_elements_by_css_selector('frame#mainFrame'):
        driver.switch_to_frame('mainFrame')

    token = None
    while not token:
        if driver.find_elements_by_name('coinhive-captcha-token'):
            token = driver.find_element_by_name('coinhive-captcha-token').get_attribute('value')
        time.sleep(1)


def login(driver, guy):
    log('trying to login')
    driver.get(config.LOGIN_URL)

    form = driver.find_element_by_name('form1')
    email = driver.find_element_by_name('email')
    password = driver.find_element_by_name('password')

    email.send_keys(guy.email)
    password.send_keys(guy.password or universal_password or config.PASSWORD)

    time.sleep(config.SLEEP_AFTER_LOGIN or 2)

    solve_captcha(config.LOGIN_URL, driver)
    form.submit()

    log('logged in')


def fire(driver, guy):
    if driver.find_elements_by_css_selector('frame#mainFrame'):
        driver.switch_to_frame('mainFrame')

    if driver.find_elements_by_css_selector('form#captcha'):
        form = driver.find_element_by_id('captcha')

        if driver.find_elements_by_tag_name('iframe'):
            solve_captcha(surf_url(guy), driver)

        form.submit()
    else:
        driver.switch_to_default_content()
        if driver.find_elements_by_css_selector('frame#mainFrame'):
            driver.switch_to_frame('mainFrame')
            driver.switch_to_frame('header')

        while len(driver.find_element_by_id('count').text) < 3:
            time.sleep(1)

        if not driver.find_elements_by_css_selector('span#com font'):
            time.sleep(3)

        color = driver.find_element_by_css_selector('span#com font').text
        button = driver.find_element_by_xpath('//button[@title="{}"]'.format(color))

        guy.pages = int(driver.find_elements_by_css_selector('div[title*="surfed today"]')[2].text)

        button.click()

        driver.switch_to_default_content()

        return True


def setup_driver():
    try:
        chrome_options = Options()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument('--webdriver-logfile=webdrive.log')

        prefs = {'profile.managed_default_content_settings.images': 2}
        chrome_options.add_experimental_option('prefs', prefs)

        dc = DesiredCapabilities.CHROME
        dc['loggingPrefs'] = {'browser': 'ALL'}

        driver = webdriver.Chrome(chrome_options=chrome_options,
                                  desired_capabilities=dc)

        max_wait = config.LOAD_TIMEOUT
        driver.set_window_size(500, 500)
        driver.set_page_load_timeout(max_wait)
        driver.set_script_timeout(max_wait)
    except Exception as e:
        ipdb.set_trace()

    def handler(*args):
        if config.DEBUG:
            ipdb.set_trace()
        else:
            try:
                if driver:
                    driver.stop_client()
                    driver.close()
                    driver.quit()
            except:
                log('quitting')

        signal.signal(signal.SIGINT, signal.SIG_IGN)

    signal.signal(signal.SIGINT, handler)

    return driver


def run(guy):
    pages_surfed = 0
    driver = setup_driver()
    log('boosting {}:'.format(guy), guy=guy)

    login(driver, guy)
    driver.get(surf_url(guy))

    while getattr(guy, 'pages', pages_surfed) < 100:
        try:
            if fire(driver, guy):
                pages_surfed += 1
                log('pages surfed: {}'.format(pages_surfed))

        except Exception as e:
            log(e, type='error')

    driver.quit()

class Guy(dict):
    def __init__(self, guy):
        self.__dict__.update(**guy)
        self.it = guy

    def __getattr__(self, name):
        return self[name] if name in self else None

    def __setattr__(self, name, value):
        self[name] = value

    def __repr__(self):
        return 'Guy({})'.format(self.it)


def main():
    log('welcome!')
    global password

    # password = select.select([getpass.getpass('pass?\n')], [], [], 10)

    for g in config.GUYS:
        run(Guy(g))

try:
    main()
except (socket.error,
        KeyboardInterrupt,
        http.client.RemoteDisconnected):
    log('bye!'.format(solved_captchas))
