from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_get_centres_with_available_tests():
    response = client.get("/centres/")

    assert response.status_code == 200

    centres = response.json()

    assert len(centres) >= 2

    first_centre = centres[0]

    assert "id" in first_centre
    assert "name" in first_centre
    assert "location" in first_centre
    assert len(first_centre["tests"]) > 0

    first_test = first_centre["tests"][0]

    assert "id" in first_test
    assert "name" in first_test
    assert "price" in first_test