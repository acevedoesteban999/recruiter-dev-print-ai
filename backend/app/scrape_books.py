import os
import json
import logging
from .src.scrape_base import ScrapeBase
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import redis
from dotenv import load_dotenv
from urllib.parse import urljoin


# Configure logging as required by project specifications
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env file


class BookScraper(ScrapeBase):
    """Scrapes book data from target website and stores in Redis"""

    def __init__(self):
        super().__init__()
        # Initialize Redis connection with environment variables
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", 'localhost'),  # Default to localhost if not set
            port=self.__str_2_int(os.getenv("REDIS_PORT")),  # Convert port to int
            db=0  # Using default Redis database
        )
        # Verify Redis connection
        if (not self.redis_client.ping()):
            logger.error("Redis Error: Server dont response correctly")

        # Initialize scraping counters and configuration
        self.scraped_books = 0
        self.BASE_BOOKS_URL = str(os.getenv("BASE_BOOKS_URL", ""))  # Base URL for book scraping
        self.MAX_PRICE = self.__str_2_int(os.getenv("MAX_PRICE", "20"))  # Max book price filter
        self.MAX_BOOKS = self.__str_2_int(os.getenv("MAX_BOOKS", "100"))  # Upper limit for books
        self.MIN_BOOKS = self.__str_2_int(os.getenv("MIN_BOOKS", "50"))  # Minimum books required

    def _scrape_book_details(self, book_url: str):
        """Scrapes detailed information from individual book page"""
        self.driver.get(book_url)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        try:
            # Extract book details with error handling
            title = soup.find("h1").text
            price = float(soup.find("p", class_="price_color").text[1:])  # Remove currency symbol
            category = soup.find("ul", class_="breadcrumb").find_all("a")[2].text
            image_url = self.BASE_BOOKS_URL + soup.find("img")["src"].replace("../", "")
        except Exception:
            return False  # Return False if any extraction fails

        return {
            "title": title,
            "price": price,
            "category": category,
            "image_url": image_url
        }

    def scrape_books(self):
        """Main scraping method that handles pagination and data storage"""
        logger.info("Init scraping")
        try:
            self.driver.get(self.BASE_BOOKS_URL)

            while self.scraped_books < self.MAX_BOOKS:
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                page_books = soup.find_all("article", class_="product_pod")
                current_url = self.driver.current_url

                try:
                    # Find next page URL if available
                    next_url = self.driver.find_element(
                        By.CSS_SELECTOR, "li.next > a").get_attribute('href')
                except Exception:
                    next_url = None  # No more pages if next button not found

                # Process books on current page
                for _, article in enumerate(page_books):
                    price = float(article.find("p", class_="price_color").text[1:])
                    if price >= self.MAX_PRICE:
                        continue  # Skip books over price limit

                    book_url: str = article.find("div", class_="image_container").find("a")["href"]
                    book_url = urljoin(current_url, book_url)  # Build absolute URL

                    book_data = self._scrape_book_details(book_url)
                    if not book_data:
                        continue  # Skip if book details couldn't be extracted

                    # Generate book ID from URL
                    book_id = book_url.split('_')[-1].split('/')[0]

                    # Store book data in Redis
                    self.redis_client.set(f"book:{book_id}", json.dumps(book_data))
                    self.scraped_books += 1
                    logger.info(
                        f"Book #{self.scraped_books}: {book_data['title']} (£{book_data['price']})")

                    if self.scraped_books >= self.MAX_BOOKS:
                        break  # Stop if max books reached

                logger.info(f"Scraped {self.scraped_books} books in page {current_url}")

                # Pagination logic
                if self.scraped_books < self.MIN_BOOKS:
                    if next_url:
                        self.driver.get(next_url)  # Go to next page if minimum not met
                    else:
                        logger.warning(
                            f"Unsatisfied minimal books; Books find: {self.scraped_books}")
                        break
                else:
                    break  # Stop if minimum books requirement is satisfied

        except Exception as e:
            logger.error(f"Scraping Error: {e}")

        logger.info(f"Scraping Commpleted. Books find: {self.scraped_books}")

    @staticmethod
    def __str_2_int(_str: str | None) -> int:
        """Safe conversion from string to integer with fallback to 0"""
        try:
            return int(_str) if _str else 0
        except Exception:
            return 0
