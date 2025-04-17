import logging
import os
from .src.scrape_base import ScrapeBase
from selenium.webdriver.common.by import By

# Configure logging as per project requirements
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HackerNewsScraper(ScrapeBase):
    """Scraper for Hacker News top stories with real-time fetching"""

    def __init__(self) -> None:
        super().__init__()
        # Base URL from environment variables with fallback to empty string
        self.BASE_NEWS_URL = str(os.getenv("BASE_NEWS_URL", ""))

    # TODO Addapt to n8n finaly development

    def scrape_top_stories(self, pages: int = 5):
        """
        Scrape top stories from Hacker News
        Args:
            pages: Number of pages to scrape (default: 5)
        Returns:
            List of dictionaries containing story details
        """
        stories = []

        try:
            # Iterate through specified number of pages
            for page in range(1, pages + 1):
                url = f"{self.BASE_NEWS_URL}?p={page}"
                logger.info(f"Scraping page: {url}")

                self.driver.get(url)

                # Find all story rows (elements with class 'athing')
                rows = self.driver.find_elements(By.CLASS_NAME, "athing")

                for row in rows:
                    try:
                        # Extract title and URL from titleline
                        title_elem = row.find_element(
                            By.CLASS_NAME, "titleline")
                        title = title_elem.find_element(By.TAG_NAME, "a").text
                        url = title_elem.find_element(
                            By.TAG_NAME, "a").get_attribute("href")

                        # Extract score from following sibling row
                        score_elem = row.find_element(
                            By.XPATH, "./following-sibling::tr")
                        if score_elem.find_elements(By.CLASS_NAME, "score"):
                            score = score_elem.find_element(
                                By.CLASS_NAME, "score").text.split()[0]
                        else:
                            score = "0"  # Default score if not present

                        stories.append({
                            "title": title,
                            "score": int(score),  # Convert score to integer
                            "url": url
                        })
                    except Exception as e:
                        logger.warning(f"Error processing story: {str(e)}")
                        continue  # Skip to next story if error occurs

        except Exception as e:
            logger.error(f"Unexpected error during scraping: {str(e)}")

        logger.info(f"Scraping Success: News: {len(stories)}")
        return stories
