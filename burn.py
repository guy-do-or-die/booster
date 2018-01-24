import re
import ipdb
import time
import names
import signal
import logging

from datetime import datetime

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask

from stem.control import Controller
from stem import Signal

from utils import wait, element_has_attribute

from db import Guy

import config

anticpatcha_client = AnticaptchaClient(config.API_KEY)
solved_captchas = 0


def now():
    return datetime.now().strftime('%Y.%m.%d %H:%M:%S')


logging.basicConfig(filename='logs/{}.log'.format(now()),
                    format=config.LOG_FORMAT,
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)

if config.DEBUG:
    LOGGER.setLevel(logging.WARNING)


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


def surf_url(guy):
    return config.SURF_URL.format(guy.ref_id)


def reconn():
    with Controller.from_port(port=config.TOR_PORT) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)


def switch(driver, frame):
    driver.switch_to.default_content()

    if driver.find_elements_by_css_selector('frame#mainFrame'):
        driver.switch_to_frame('mainFrame')
    '''
    if driver.find_elements_by_css_selector('iframe[name*="mainiFrame"]'):
        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, 'iframe[name*="mainiFrame"]'))
    '''
    if frame == 'header' and driver.find_elements_by_css_selector('frame[name="header"]'):
        driver.switch_to_frame('header')

    if frame == 'captcha' and driver.find_elements_by_css_selector('iframe[src*="captcha"]'):
        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, 'iframe[src*="captcha"]'))

    if frame == 'mainiFrame':
        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, 'iframe[name*="mainiFrame"]'))


def solve_captcha(driver):
    if driver.find_elements_by_class_name('g-recaptcha'):
        captcha = driver.find_element_by_class_name('g-recaptcha')
        site_key = captcha.get_attribute('data-sitekey')
        log('recaptcha found')

        if not site_key:
            site_key = driver.find_element_by_css_selector(
                '.challenge-form script').get_attribute('data-sitekey')

        task = NoCaptchaTaskProxylessTask(website_url=driver.current_url, website_key=site_key)
        job = anticpatcha_client.createTask(task)
        job.join()

        token = job.get_solution_response()

        global solved_captchas
        solved_captchas += 1

        log('recaptcha solved ({})'.format(solved_captchas))

        wait(driver, EC.presence_of_element_located((By.CSS_SELECTOR, '#g-recaptcha-response')))
        driver.execute_script('document.getElementById("g-recaptcha-response").value="{}"'.format(token))
    else:
        switch(driver, 'mainFrame')
        switch(driver, 'captcha')

        if (driver.find_elements_by_css_selector('.verify-me-progress[role="checkbox"]')
            and not driver.find_elements_by_css_selector('checkmark')):

            wait(driver, EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.verify-me-progress[role="checkbox"]'))).click()

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

    solve_captcha(driver)
    form.submit()

    log('logged in')


def fire(driver, guy):
    switch(driver, 'mainFrame')

    if re.search(r'wait 15 seconds and then reload', driver.page_source):
        time.sleep(15); driver.get(surf_url(guy))

    if driver.find_elements_by_css_selector('frame[name="header"]'):
        switch(driver, 'header')

        guy.pages_today = int(driver.find_elements_by_css_selector('div[title*="surfed today"]')[2].text)

        wait(driver, EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'button[onclick*="submitform"]'))).click()

        switch(driver, 'mainFrame')

        try:
            wait(driver, EC.presence_of_element_located((By.CSS_SELECTOR, '#captcha')))
        except:
            wait(driver, EC.presence_of_element_located((By.CSS_SELECTOR, '#captcha')))

        return True
    else:
        form = driver.find_element_by_id('captcha')

        if driver.find_elements_by_tag_name('iframe'):
            solve_captcha(driver)

        form.submit()


def setup_driver(proxy=False):
    try:
        chrome_options = Options()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--mute-audio')

        prefs = {'profile.managed_default_content_settings.images': 2}
        chrome_options.add_experimental_option('prefs', prefs)
        chrome_options.add_experimental_option('detach', False)

        dc = DesiredCapabilities.CHROME
        dc['loggingPrefs'] = {'browser': 'ALL'}

        if proxy:
            proxy = Proxy()
            proxy.proxy_type = ProxyType.MANUAL
            proxy.socks_proxy = config.PROXY
            proxy.http_proxy = config.PROXY
            proxy.ssl_proxy = config.PROXY
            proxy.add_to_capabilities(dc)

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


def stat(guy, driver=None):
    if not driver:
        driver = setup_driver()
        login(driver, guy)

    driver.get(config.STAT_URL)

    switch(driver, 'mainiFrame')

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

    try:
        guy.save()
    except Exception as e:
        log(e, type='error')

    driver.quit()


def prop():
    pass


def pref(driver):
    driver.get(config.PREFERENCE_URL)
    driver.find_elements_by_css_selector('input[name="ico"] + span')[-1].click()
    driver.find_elements_by_css_selector('input[name="captcha"] + span')[0].click()
    driver.find_element_by_name('form1').submit()


def reg(guy, num):
    for n in range(len(guy.refs), num):
        g = Guy(
            ref_name=guy.next_ref_name(n),
            name=names.get_first_name(),
            email=guy.next_email(n),
            level=guy.level + 1,
            ref=guy
        )

        reconn()
        driver = setup_driver(proxy=True)
        driver.get('{}/{}'.format(config.URL, guy.ref_name))

        solve_captcha(driver)
        driver.find_element_by_css_selector('form').submit()

        driver.find_element_by_xpath("//a[contains(text(), 'Register')]").click()
        time.sleep(1)

        wait(driver, EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'input[name="email"]'))).send_keys(g.email)

        solve_captcha(driver)
        driver.find_element_by_css_selector('button[type="submit"]').click()

        wait(driver, EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'input[name="first_name"]'))).send_keys(g.name)

        ref_name_input = driver.find_element_by_css_selector('input[name="foldername"]')
        ref_name_input.clear(); ref_name_input.send_keys(g.ref_name)

        driver.find_element_by_css_selector('input[name="pass"]').send_keys(config.PASSWORD)
        driver.find_element_by_css_selector('input[name="cpass"]').send_keys(config.PASSWORD)
        driver.find_element_by_css_selector('input[name="terms"]').click()
        driver.find_element_by_css_selector('button[type="submit"]').click()

        switch(driver, 'mainiFrame')  # !!!!
        if driver.find_elements_by_id('menu-toggler'):
            driver.find_element_by_id('menu-toggler').click()
            time.sleep(0.5)

        g.ref_id = driver.find_element_by_css_selector(
            'a[href*="recommends"]').get_attribute('href').split('=')[-1]

        pref(driver)
        driver.quit()
        g.save()

        guy.refs.append(g)
        guy.save()

        log('created one more guy!', guy=g)


def surf(guy):
    fail = 0
    pages_surfed = 0
    driver = setup_driver()
    log('boosting!', guy=guy)
    login(driver, guy)

    if guy.pages_today >= config.PAGE_RATES[guy.level]:
        guy.pages_today = 0

    if guy.level == 2:
        pref(driver)

    driver.get(surf_url(guy))

    while guy.pages_today < config.PAGE_RATES[guy.level] and fail < 5:
        try:
            if fire(driver, guy):
                pages_surfed += 1
                guy.pages_today += 1

                log('pages surfed: {}/{}'.format(
                    pages_surfed, guy.pages_today), guy=guy)

        except Exception as e:
            log(e, type='error')
            log('fail: {}'.format(fail), guy=guy)

            if fail < 3:
                time.sleep(config.SLEEP_ON_ERROR)
                fail += 1
            else:
                driver.get(surf_url(guy))

            if config.DEBUG:
                ipdb.set_trace()

    stat(guy, driver)
    driver.quit()
