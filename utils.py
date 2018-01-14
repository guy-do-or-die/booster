from selenium.webdriver.support.ui import WebDriverWait

import config


class element_has_attribute(object):
    def __init__(self, locator, attribute):
        self.attribute = attribute
        self.locator = locator

    def __call__(self, driver):
        element = driver.find_element(*self.locator)
        return element.get_attribute(self.attribute)


def wait(driver, *args, **kwargs):
    return WebDriverWait(driver, config.LOAD_TIMEOUT).until(*args, **kwargs)
