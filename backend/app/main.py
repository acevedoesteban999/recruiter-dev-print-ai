from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import redis
import json
import os
from typing import List, Optional
from .scrape_hn import HackerNewsScraper
from .scrape_books import BookScraper
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for data validation


class Book(BaseModel):
    id: str
    title: str
    price: float
    category: str
    image_url: str


class HNStory(BaseModel):
    title: str
    score: int
    url: str


# Redis configuration
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", 'localhost'),
    port=os.getenv("REDIS_PORT"),
    db=0
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        if not os.getenv("DEV_MODE", False):
            await init_scraping()
    except Exception:
        logger.error("Error during scraping initialization: lifespan")

    yield

app = FastAPI(
    title="Print.AI Technical Assessment API",
    description="API for the web scraping and Hacker News integration system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/init", status_code=status.HTTP_200_OK)
async def init_scraping():
    """Endpoint to force book re-scraping (maintained for compatibility)"""
    try:
        book_scraper = BookScraper()
        book_scraper.scrape_books()
        return {"message": "Scraping initialization completed"}
    except Exception as e:
        logger.error(f"Error in init_scraping: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scraping initialization failed"
        )


@app.get("/books/search", response_model=List[Book])
async def search_books(
    title: Optional[str] = None,
    category: Optional[str] = None,
    max_price: Optional[float] = 20.0
):
    """
    Search books by title, category and max price (default £20)
    Supports partial matches in title (case insensitive)

    Examples:
    - /books/search?title=mystery
    - /books/search?category=fiction&max_price=15
    - /books/search?title=harry&category=fantasy
    """
    try:
        books = []
        for key in redis_client.scan_iter("book:*"):
            book_data = redis_client.get(key)
            if not book_data:
                continue

            book = json.loads(book_data)

            match = True

            if title:
                match = match and (title.lower() in book["title"].lower())

            if category:
                match = match and (category.lower() ==
                                   book["category"].lower())

            if max_price is not None:
                match = match and (book["price"] <= max_price)

            if match:
                books.append(Book(
                    id=key.decode().split(":")[1],
                    title=book["title"],
                    price=book["price"],
                    category=book["category"],
                    image_url=book["image_url"]
                ))

        return books

    except Exception as e:
        logger.error(f"Error in search_books: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching books"
        )


@app.get("/headlines", response_model=List[HNStory])
async def get_headlines():
    """
    Get current top stories from Hacker News (real-time, no caching)
    Example: /headlines
    """
    try:
        scraper = HackerNewsScraper()
        headlines = scraper.scrape_top_stories()
        return [HNStory(**story) for story in headlines]
    except Exception as e:
        logger.error(f"Error in get_headlines: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not fetch Hacker News headlines"
        )
    finally:
        if 'scraper' in locals():
            scraper._close_selenium()


@app.get("/books", response_model=List[Book])
async def get_books(category: Optional[str] = None):
    """
    Get all books (optionally filtered by category)
    Example: /books?category=fiction
    """
    try:
        books = []
        for key in redis_client.scan_iter("book:*"):
            book_data = redis_client.get(key)
            if book_data:
                book = json.loads(book_data)
                if not category or category.lower() == book["category"].lower():
                    books.append(Book(
                        id=key.decode().split(":")[1],
                        title=book["title"],
                        price=book["price"],
                        category=book["category"],
                        image_url=book["image_url"]
                    ))

        return books

    except Exception as e:
        logger.error(f"Error in get_books: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving books"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
