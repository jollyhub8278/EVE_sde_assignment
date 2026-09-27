from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from src.main import app
from src.models.user import User
from src.utils.db import SessionLocal

client = TestClient(app)


def delete_test_user(email: str):
    db = SessionLocal()

    try:
        user = db.scalar(select(User).where(User.email == email))

        if user:
            db.delete(user)
            db.commit()
    finally:
        db.close()


def test_signup_creates_user():
    email = f"test_{uuid4().hex}@example.com"

    try:
        response = client.post(
            "/auth/signup",
            json={
                "name": "Test User",
                "email": email,
                "password": "password123",
            },
        )

        assert response.status_code == 201
        assert response.json()["user"]["email"] == email

        db = SessionLocal()

        try:
            user = db.scalar(select(User).where(User.email == email))

            assert user is not None
            assert user.hashed_password != "password123"
        finally:
            db.close()
    finally:
        delete_test_user(email)


def test_signup_rejects_duplicate_email():
    email = f"duplicate_{uuid4().hex}@example.com"

    try:
        payload = {
            "name": "Test User",
            "email": email,
            "password": "password123",
        }

        first_response = client.post("/auth/signup", json=payload)
        second_response = client.post("/auth/signup", json=payload)

        assert first_response.status_code == 201
        assert second_response.status_code == 409
        assert second_response.json()["detail"] == "Email is already registered"
    finally:
        delete_test_user(email)