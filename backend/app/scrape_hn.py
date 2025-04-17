import logging
import os
from src.scrape_base import ScrapeBase
from selenium.webdriver.common.by import By

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HackerNewsScraper(ScrapeBase):
    def __init__(self) -> None:
        super().__init__()
        self.BASE_NEWS_URL = str(os.getenv("BASE_NEWS_URL", ""))

    def scrape_top_stories(self, pages: int = 5):

        stories = []

        try:
            for page in range(1, pages + 1):
                url = f"{self.BASE_NEWS_URL}?p={page}"
                logger.info(f"Scraping page: {url}")

                self.driver.get(url)

                rows = self.driver.find_elements(By.CLASS_NAME, "athing")

                for row in rows:
                    try:
                        title_elem = row.find_element(
                            By.CLASS_NAME, "titleline")
                        title = title_elem.find_element(By.TAG_NAME, "a").text
                        url = title_elem.find_element(
                            By.TAG_NAME, "a").get_attribute("href")

                        score_elem = row.find_element(
                            By.XPATH, "./following-sibling::tr")
                        if score_elem.find_elements(By.CLASS_NAME, "score"):
                            score = score_elem.find_element(
                                By.CLASS_NAME, "score").text.split()[0]
                        else:
                            score = "0"

                        stories.append({
                            "title": title,
                            "score": int(score),
                            "url": url
                        })
                    except Exception as e:
                        logger.warning(f"Error: {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
        logger.info(f"Scraping Success: News: {len(stories)}")
        return stories


if __name__ == "__main__":
    scraper = HackerNewsScraper()
    headlines = scraper.scrape_top_stories()
    scraper._close_selenium()
