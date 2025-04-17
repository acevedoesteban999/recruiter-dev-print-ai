import pytest
from fastapi.testclient import TestClient
from app.main import app
from redis import Redis

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_redis(mocker):
    mock = mocker.MagicMock(spec=Redis)
    mocker.patch("app.redis_client.redis", mock)
    return mock