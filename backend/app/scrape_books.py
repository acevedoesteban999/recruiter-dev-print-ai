import os
import json
import time
import logging
from typing import Dict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import redis
from dotenv import load_dotenv

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
            port=os.getenv("REDIS_PORT",6379),
            db=0
        )
        self.driver = self._init_selenium()
        self.scraped_books = 0
        self.BASE_URL = str(os.getenv("BASE_URL",""))
        self.MAX_PRICE = self.__str_2_int(os.getenv("MAX_PRICE","5"))
        self.MAX_BOOKS = self.__str_2_int(os.getenv("MAX_BOOKS","100"))
        self.MIN_BOOKS = self.__str_2_int(os.getenv("MIN_BOOKS","50"))

    def _init_selenium(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        return webdriver.Chrome(
            service=Service(webdriver.ChromeService()),
            options=chrome_options,
        )

    def _scrape_book_details(self, book_url: str) -> Dict:
        self.driver.get(book_url)
        time.sleep(1)  
        soup = BeautifulSoup(self.driver.page_source, "lxml")
        
        title = soup.find("h1").text
        price = float(soup.find("p", class_="price_color").text[1:]) 
        category = soup.find("ul", class_="breadcrumb").find_all("a")[2].text
        image_url = self.BASE_URL + soup.find("img")["src"].replace("../", "")
        
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
                soup = BeautifulSoup(self.driver.page_source, "lxml")
                page_books = soup.find_all("article", class_="product_pod")
                
                for _,book in enumerate(page_books):
                    price = float(book.find("p", class_="price_color").text[1:])
                    if price >= self.MAX_PRICE:
                        continue
                    book_url = self.BASE_URL + "catalogue/" + book.find("h3").find("a")["href"].replace("../", "")
                    book_data = self._scrape_book_details(book_url)
                    
                    book_id = hash(book_url) % 1000000
                    self.redis_client.set(f"book:{book_id}", json.dumps(book_data))
                    self.scraped_books += 1
                    logger.info(f"Book #{self.scraped_books}: {book_data['title']} (£{book_data['price']})")
                    
                    self.scraped_books += 1
                    if self.scraped_books >= self.MAX_BOOKS:
                        break
                if self.scraped_books < self.MIN_BOOKS:
                    next_btn = self.driver.find_elements(By.CSS_SELECTOR, "li.next a")
                    if not next_btn:
                        logger.warning(f"Unsatisfied minimal books; Books find: {self.scraped_books}")
                        break
                    next_btn[0].click()
                    time.sleep(2)
                else:
                    break

            logger.info(f"Scraping Commpleted. Books find: {self.scraped_books}")
        except Exception as e:
            logger.error(f"Scraping Error: {e}")
        self.driver.quit()
            
if __name__ == "__main__":
    scraper = BookScraper()
    scraper.scrape_books()