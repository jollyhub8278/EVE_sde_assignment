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
        
def test_login_returns_access_token():
    email = f"login_{uuid4().hex}@example.com"

    try:
        signup_response = client.post(
            "/auth/signup",
            json={
                "name": "Login Test User",
                "email": email,
                "password": "password123",
            },
        )

        assert signup_response.status_code == 201

        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "password123",
            },
        )

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    finally:
        delete_test_user(email)

def test_login_rejects_wrong_password():
    email = f"wrong_password_{uuid4().hex}@example.com"

    try:
        client.post(
            "/auth/signup",
            json={
                "name": "Wrong Password Test",
                "email": email,
                "password": "password123",
            },
        )

        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"
    finally:
        delete_test_user(email)
        
def test_get_my_profile_with_valid_token():
    email = f"profile_{uuid4().hex}@example.com"

    try:
        client.post(
            "/auth/signup",
            json={
                "name": "Profile Test User",
                "email": email,
                "password": "password123",
            },
        )

        login_response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "password123",
            },
        )

        token = login_response.json()["access_token"]

        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Profile Test User"
        assert response.json()["email"] == email
    finally:
        delete_test_user(email)


def test_get_my_profile_requires_token():
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"