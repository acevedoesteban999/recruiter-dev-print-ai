import os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager


class ScrapeBase():

    def __init__(self) -> None:
        _options = Options()
        _options.binary_location = str(os.getenv("FIREFOX_DRIVER_PATH", ""))
        # _options.add_argument("--headless")
        # _options.add_argument("--no-sandbox")
        self.driver = webdriver.Firefox(
            service=Service(GeckoDriverManager().install()),
            options=_options,
        )

    def _close_selenium(self):
        if self.driver:
            self.driver.quit()
