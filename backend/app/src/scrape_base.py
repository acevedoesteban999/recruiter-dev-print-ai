from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class ScrapeBase():
    """This class implement init and close for selenium"""
    def __init__(self) -> None:
        _options = Options()
        # _options.binary_location = str(os.getenv("WEBDRIVER_PATH", ""))
        _options.add_argument("--headless")
        _options.add_argument("--no-sandbox")
        self.driver = webdriver.Firefox(
            service=Service(ChromeDriverManager().install()),
            options=_options,
        )

    def _close_selenium(self):
        if self.driver:
            self.driver.quit()
