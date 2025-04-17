import pytest
import httpx
import dotenv
import os
from typing import List
dotenv.load_dotenv()


@pytest.mark.asyncio
async def test_get_books_search_endpoint():
    async with httpx.AsyncClient(
            base_url=f'{os.getenv("FASTAPI_HOST","http://localhost")}:{os.getenv("FASTAPI_PORT","7013")}') as client:
        response = await client.get("/books/search")
        assert response.status_code == 200
        books_data = response.json()
        assert isinstance(books_data, List)


@pytest.mark.asyncio
async def test_get_books_endpoint():
    async with httpx.AsyncClient(
            base_url=f'{os.getenv("FASTAPI_HOST")}:{os.getenv("FASTAPI_PORT","7013")}') as client:
        response = await client.get("/books")
        assert response.status_code == 200
        assert response.json()
