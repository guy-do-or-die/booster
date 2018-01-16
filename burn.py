import ipdb
import time
import signal
import logging

from datetime import datetime
from itertools import zip_longest

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from stem.control import Controller
from stem import Signal

from utils import wait, element_has_attribute

import config

universal_password = None


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
    message, ' ({}, {})'.format(guy.name, guy.ref_id) if guy else '')

    print('{}: {}'.format(now(), message))
    getattr(logger, type)(message, extra=kwargs)

    if config.DEBUG and type == 'error':
        driver = kwargs.get('driver')
        config.DEBUG and ipdb.set_trace()


def reconn():
    with Controller.from_port(port=config.TOR_PORT) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)


def surf_url(guy):
    return config.SURF_URL.format(guy.ref_id)


def switch(driver, frame):
    driver.switch_to.default_content()

    if driver.find_elements_by_css_selector('frame#mainFrame'):
        driver.switch_to_frame('mainFrame')

    if frame == 'header' and driver.find_elements_by_css_selector('frame[name="header"]'):
        driver.switch_to_frame('header')

    if frame == 'captcha' and driver.find_elements_by_css_selector('iframe[src*="captcha"]'):
        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, "iframe[src*='captcha']"))

    if frame == 'stat':
        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, "iframe[name*='mainiFrame']"))


def solve_captcha(url, driver):
    switch(driver, 'mainFrame')
    switch(driver, 'captcha')

    if not driver.find_elements_by_css_selector('checkmark'):
        wait(driver, EC.presence_of_element_located((By.CSS_SELECTOR, 'div[id="verify-me"]'))).click()

    switch(driver, 'mainFrame')

    wait(driver, element_has_attribute((By.NAME, 'coinhive-captcha-token'), 'value'))


def login(driver, guy):
    log('trying to login')
    driver.get(config.LOGIN_URL)

    form = driver.find_element_by_name('form1')
    email = driver.find_element_by_name('email')
    password = driver.find_element_by_name('password')

    email.send_keys(guy.email)
    password.send_keys(config.PASSWORD)

    solve_captcha(config.LOGIN_URL, driver)
    form.submit()

    log('logged in')


def fire(driver, guy):
    switch(driver, 'mainFrame')

    if driver.find_elements_by_css_selector('form#captcha'):
        form = driver.find_element_by_id('captcha')

        if driver.find_elements_by_tag_name('iframe'):
            solve_captcha(surf_url(guy), driver)

        form.submit()
    else:
        switch(driver, 'header')

        guy.pages_today = int(driver.find_elements_by_css_selector(
            'div[title*="surfed today"]')[2].text)

        wait(driver, EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'button[onclick*="submitform"]'))).click()

        switch(driver, 'mainFrame')

        wait(driver, EC.presence_of_element_located((By.CSS_SELECTOR, 'form#captcha')))

        return True


def setup_driver():
    try:
        chrome_options = Options()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--webdriver-logfile=webdrive.log')
        #chrome_options.add_argument('--proxy-server=127.0.0.1:8118')

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
        config.DEBUG and ipdb.set_trace()

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


def surf(guy):
    pages_surfed = 0
    driver = setup_driver()
    log('boosting!', guy=guy)

    login(driver, guy)

    driver.get(surf_url(guy))

    fail = 0
    while getattr(guy, 'pages_today') or pages_surfed < config.PAGES_PER_DAY:
        try:
            if fire(driver, guy):
                pages_surfed += 1
                guy.pages_today += 1

                log('pages surfed: {}/{}'.format(
                    pages_surfed, guy.pages_today), guy=guy)

        except Exception as e:
            log(e, type='error')
            if fail < 1:
                time.sleep(config.SLEEP_ON_ERROR)
                fail += 1

            driver.get(surf_url(guy))
            fail = 0

    stat(g, driver)

    driver.quit()


def stat(guy, driver=None):
    if not driver:
        driver = setup_driver()
        login(driver, guy)

    driver.get(config.STAT_URL)

    switch(driver, 'stat')

    for row in driver.find_elements_by_tag_name('tr'):
        title, data = (cell.text for cell in row.find_elements_by_tag_name('td'))

        if 'Pages Surfed Today' in title:
            guy.pages_today = int(data.split('\n')[0])

        if 'Total Pages Surfed' in title:
            guy.pages_total = int(data.replace(',', ''))

        if 'Shares Earned Today' in title:
            guy.shares_today = int(data)

        if 'Current Earnings' in title:
            guy.earnings = float(data[-10:])

    guy.updated = datetime.now()
    guy.level = 2

    try:
        guy.save()
    except Exception as e:
        log(e, type='error')

    driver.quit()


def prop():
    pass


def reg(g, num):
    pass
