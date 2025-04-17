from fastapi import status
from app.models import BookModel  # Ajusta según tus modelos Pydantic

def test_init_scraping(client, mock_redis):
    # Simula Redis y verifica el endpoint /init
    mock_redis.keys.return_value = []
    response = client.post("/init")
    assert response.status_code == status.HTTP_200_OK
    assert "Scraping completed" in response.json()["message"]

def test_search_books(client, mock_redis):
    # Mock de datos en Redis
    mock_redis.keys.return_value = [b"book:1"]
    mock_redis.get.return_value = '{"title": "Python Book", "price": 15.99, "category": "Programming"}'
    
    response = client.get("/books/search?query=Python")
    assert response.status_code == status.HTTP_200_OK
    assert "Python Book" in response.json()[0]["title"]

def test_headlines_realtime(client, mocker):
    # Mock de Selenium para Hacker News
    mocker.patch("app.scraper.scrape_hn", return_value=[{"title": "News 1", "score": 100}])
    response = client.get("/headlines")
    assert response.status_code == status.HTTP_200_OK
    assert "News 1" in response.json()[0]["title"]