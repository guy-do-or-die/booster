#! .env/bin/python

import ipdb
import time
import http
import socket
import signal
import getpass
import requests

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options

from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask

import config


anticpatcha_client = AnticaptchaClient(config.API_KEY)

universal_password = None
solved_captchas = 0


def surf_link(guy):
    return config.TARGET_URL.format(guy.id)


def solve_captcha(url, driver):
    try:
        captcha = driver.find_element_by_class_name('g-recaptcha')

        print('captcha found')
        site_key = captcha.get_attribute('data-sitekey')

        task = NoCaptchaTaskProxylessTask(website_url=url, website_key=site_key)
        job = anticpatcha_client.createTask(task)
        job.join()

        token = job.get_solution_response()

        global solved_captchas
        solved_captchas += 1

        print('captcha solved ({})'.format(solved_captchas))

        driver.execute_script('document.getElementById("g-recaptcha-response").value="{}"'.format(token))

        return True
    except Exception as e:
        print('no captcha', e)
        return False


def login(driver, guy):
    print('trying to login')
    driver.get(config.LOGIN_URL)

    form = driver.find_element_by_name('form1')
    email = driver.find_element_by_name('email')
    password = driver.find_element_by_name('password')

    email.send_keys(guy.email)
    password.send_keys(guy.password or universal_password or config.PASSWORD)

    time.sleep(config.SLEEP_AFTER_LOGIN or 2)

    if solve_captcha(config.LOGIN_URL, driver):
        form.submit()

        driver.get(surf_link(guy))

        print('logged in')
        return True
    else:
        print('failed to login')
        return False


def fire(driver, guy):
    try:
        form = driver.find_element_by_id('captcha')

        solve_captcha(surf_link(guy), driver)
        form.submit()
    except Exception as e:
        print(e)

    try:
        driver.switch_to_frame('mainFrame')
        driver.switch_to_frame('header')
    except Exception as e:
        print(e)

    try:
        while len(driver.find_element_by_id('count').text) < 3:
            time.sleep(1)
    except Exception as e:
        print(e)

    try:
        color = driver.find_element_by_css_selector('span#com font').text
        button = driver.find_element_by_xpath('//button[@title="{}"]'.format(color))
        button.click()

        time.sleep(1)
        driver.switch_to_frame('mainFrame')
    except Exception as e:
        print(e)
        return False

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
                print('quitting')

        signal.signal(signal.SIGINT, signal.SIG_IGN)

    signal.signal(signal.SIGINT, handler)

    return driver


def run(guy):
    driver = setup_driver()
    print('boosting {}:'.format(guy.name), guy)

    if login(driver, guy):
        shares_gained = 0

        while shares_gained < 10 * guy.get('shares', 10):
            try:
                if fire(driver, guy):
                    shares_gained += 1
                    print('shares gained: {}'.format(shares_gained))
                else:
                    print('retrying...')
            except Exception as e:
                print(e)
                time.sleep(config.SLEEP_ON_ERROR or 15)
                driver.get(surf_link(guy))

    driver.quit()


class Guy(dict):
    def __init__(self, guy):
        self.__dict__.update(**guy)
        self.it = guy

    def __getattr__(self, name):
        return self[name] if name in self else None

    def __repr__(self):
        return 'Guy({})'.format(self.it)


def main():
    global password

    password = getpass.getpass('pass?\n')

    for g in config.GUYS:
        run(Guy(g))

try:
    main()
except (socket.error,
        KeyboardInterrupt,
        http.client.RemoteDisconnected):
    print('captchas spent: {}, buy!'.format(solved_captchas))
