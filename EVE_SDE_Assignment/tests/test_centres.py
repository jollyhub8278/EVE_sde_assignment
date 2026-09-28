from fastapi.testclient import TestClient

from src.main import app
from uuid import uuid4

from src.models.centre import Centre
from src.models.centre_offering import CentreTest
from src.models.diagnostic import DiagnosticTest
from src.models.user import User
from src.utils.db import SessionLocal
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
    
def test_create_centre_requires_token():
    response = client.post(
        "/centres/",
        json={
            "name": "Test Diagnostics",
            "location": "Jaipur",
            "tests": [
                {
                    "name": "Vitamin B12",
                    "price": 700,
                }
            ],
        },
    )

    assert response.status_code == 401
    
def test_create_centre_with_token():
    unique_value = uuid4().hex[:8]

    email = f"centre_{unique_value}@example.com"
    password = "Password@123"
    centre_name = f"Test Centre {unique_value}"
    test_name = f"Test Profile {unique_value}"
    centre_id = None

    try:
        signup_response = client.post(
            "/auth/signup",
            json={
                "name": "Centre Test User",
                "email": email,
                "password": password,
            },
        )
        assert signup_response.status_code == 201

        login_response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        response = client.post(
            "/centres/",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "name": centre_name,
                "location": "Jaipur, Rajasthan",
                "tests": [
                    {
                        "name": test_name,
                        "price": 750,
                    }
                ],
            },
        )

        assert response.status_code == 201

        data = response.json()
        centre_id = data["id"]

        assert data["name"] == centre_name
        assert data["location"] == "Jaipur, Rajasthan"
        assert len(data["tests"]) == 1
        assert data["tests"][0]["name"] == test_name
        assert data["tests"][0]["price"] == 750.0

    finally:
        db = SessionLocal()

        try:
            if centre_id:
                db.query(CentreTest).filter(
                    CentreTest.centre_id == centre_id
                ).delete(synchronize_session=False)

                db.query(Centre).filter(
                    Centre.id == centre_id
                ).delete(synchronize_session=False)

            db.query(DiagnosticTest).filter(
                DiagnosticTest.name == test_name
            ).delete(synchronize_session=False)

            db.query(User).filter(
                User.email == email
            ).delete(synchronize_session=False)

            db.commit()

        finally:
            db.close()
    
