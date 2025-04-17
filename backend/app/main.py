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

# Configure logging as per project requirements
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for request/response validation


class Book(BaseModel):
    """Data model for book information"""
    id: str
    title: str
    price: float
    category: str
    image_url: str


class HNStory(BaseModel):
    """Data model for Hacker News stories"""
    title: str
    score: int
    url: str


# Redis connection configuration
redis_host = os.getenv("REDIS_HOST", "redis")  # Default to 'redis' for Docker
redis_port = int(os.getenv("REDIS_PORT", 6379))  # Default Redis port

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", 'localhost'),  # Fallback to localhost
    port=os.getenv("REDIS_PORT"),  # Port from environment
    db=0  # Default Redis database
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management for initialization tasks"""
    try:
        if not os.getenv("DEV_MODE", False):  # Skip in development mode
            await init_scraping()
    except Exception:
        logger.error("Error during scraping initialization: lifespan")
    yield  # Application runs here
    # Cleanup could be added here if needed

# Initialize FastAPI application with metadata
app = FastAPI(
    title="Print.AI Technical Assessment API",
    description="API for the web scraping and Hacker News integration system",
    version="1.0.0",
    docs_url="/api/docs",  # Custom docs path
    redoc_url="/api/redoc",  # Custom ReDoc path
    openapi_url="/api/openapi.json",  # Custom OpenAPI schema path
    lifespan=lifespan,  # Attach lifespan manager
)

# Configure CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (adjust for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


@app.post("/init", status_code=status.HTTP_200_OK)
async def init_scraping():
    """Endpoint to trigger book scraping (maintained for compatibility)"""
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
    Search books with filters for title, category and max price
    Supports partial title matches (case insensitive)

    Examples:
    - /books/search?title=mystery
    - /books/search?category=fiction&max_price=15
    - /books/search?title=harry&category=fantasy
    """
    try:
        books = []
        # Scan Redis for all book keys
        for key in redis_client.scan_iter("book:*"):
            book_data = redis_client.get(key)
            if not book_data:
                continue

            book = json.loads(book_data)
            match = True

            # Apply filters
            if title:
                match = match and (title.lower() in book["title"].lower())
            if category:
                match = match and (category.lower()
                                   == book["category"].lower())
            if max_price is not None:
                match = match and (book["price"] <= max_price)

            if match:
                books.append(Book(
                    id=key.decode().split(":")[1],  # Extract ID from Redis key
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

# TODO Addapt to n8n finaly development


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
        # Ensure Selenium resources are cleaned up
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
                if not category \
                        or category.lower() == book["category"].lower():
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
    """Global exception handler for uncaught exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
