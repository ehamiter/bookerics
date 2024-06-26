from .main import app
from starlette.testclient import TestClient


def test_bulk_update() -> None:
    with TestClient(app) as client:
        response = client.get("/")

        assert response.status_code == 200
        # assert b"Hello" in response.content
