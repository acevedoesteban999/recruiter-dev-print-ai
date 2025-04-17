import redis
import pytest
import dotenv
import os
dotenv.load_dotenv()

redis_client = redis.Redis(host=os.getenv(
    "REDIS_HOST"), port=os.getenv("REDIS_PORT"), decode_responses=True)


def test_redis_connection():
    response = redis_client.ping()
    assert response is True, "Redis no está activo o no responde"


def test_redis_has_keys():
    keys_count = redis_client.dbsize()
    assert keys_count > 0, "Redis está vacío, no tiene datos"
