import os
import json
import time
import logging
from typing import Dict
from bs4 import BeautifulSoup
from selenium import webdriver

from selenium.webdriver.firefox.service import Service 
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
import redis
from dotenv import load_dotenv
from urllib.parse import urljoin

# Configuración de logging (como requerido)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class BookScraper:
    @staticmethod
    def __str_2_int(_str:str|None)->int:
        try:
            return int(_str)
        except:
            return 0
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST",'localhost'),
            port=self.__str_2_int(os.getenv("REDIS_PORT")),
            db=0
        )
        if(not self.redis_client.ping()):
            logger.error(f"Redis Error: Server dont response correctly")
            
        self.driver = self._init_selenium()
        self.scraped_books = 0
        self.BASE_URL = str(os.getenv("BASE_URL",""))
        self.MAX_PRICE = self.__str_2_int(os.getenv("MAX_PRICE","5"))
        self.MAX_BOOKS = self.__str_2_int(os.getenv("MAX_BOOKS","100"))
        self.MIN_BOOKS = self.__str_2_int(os.getenv("MIN_BOOKS","50"))

    def _init_selenium(self):
        _options = Options()
        _options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"
        # _options.add_argument("--headless")
        # _options.add_argument("--no-sandbox")
        return webdriver.Firefox(
            service=Service(GeckoDriverManager().install()),
            options=_options,
        )

    def _scrape_book_details(self, book_url: str):
        self.driver.get(book_url)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        try:
            title = soup.find("h1").text
            price = float(soup.find("p", class_="price_color").text[1:]) 
            category = soup.find("ul", class_="breadcrumb").find_all("a")[2].text
            image_url = self.BASE_URL + soup.find("img")["src"].replace("../", "")
        except:
            return False
        return {
            "title": title,
            "price": price,
            "category": category,
            "image_url": image_url
        }

    def scrape_books(self):
        logger.info("Init scraping")
        try:
            self.driver.get(self.BASE_URL)
            
            while self.scraped_books < self.MAX_BOOKS:
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                page_books = soup.find_all("article", class_="product_pod")
                current_url = self.driver.current_url
                try:
                    next_url = self.driver.find_element(By.CSS_SELECTOR, "li.next > a").get_attribute('href')
                except:
                    next_url = None
                for _,article in enumerate(page_books):
                    price = float(article.find("p", class_="price_color").text[1:])
                    if price >= self.MAX_PRICE:
                        continue
                    book_url:str= article.find("div",class_="image_container").find("a")["href"]
                    book_url = urljoin(current_url, book_url)
                    book_data = self._scrape_book_details(book_url)
                    if not book_data:
                        continue
                    book_id = book_url.split('_')[-1].split('/')[0]
                    self.redis_client.set(f"book:{book_id}", json.dumps(book_data))
                    self.scraped_books += 1
                    logger.info(f"Book #{self.scraped_books}: {book_data['title']} (£{book_data['price']})")
                    if self.scraped_books >= self.MAX_BOOKS:
                        break
                if self.scraped_books < self.MIN_BOOKS:
                    if next_url:
                        self.driver.get(next_url)
                    else:
                        logger.warning(f"Unsatisfied minimal books; Books find: {self.scraped_books}")
                        break
                else:
                    break

        except Exception as e:
            logger.error(f"Scraping Error: {e}")
        
        logger.info(f"Scraping Commpleted. Books find: {self.scraped_books}")
        self.driver.quit()
            
if __name__ == "__main__":
    scraper = BookScraper()
    scraper.scrape_books()