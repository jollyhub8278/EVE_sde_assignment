from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from src.main import app
from src.models.booking import Booking
from src.models.centre_offering import CentreTest
from src.models.user import User
from src.utils.db import SessionLocal

client = TestClient(app)


def create_logged_in_user():
    email = f"booking_{uuid4().hex}@example.com"

    client.post(
        "/auth/signup",
        json={
            "name": "Booking Test User",
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

    return email, {"Authorization": f"Bearer {token}"}


def delete_booking_test_user(email: str):
    db = SessionLocal()

    try:
        user = db.scalar(select(User).where(User.email == email))

        if user:
            db.query(Booking).filter(Booking.user_id == user.id).delete()
            db.delete(user)
            db.commit()
    finally:
        db.close()


def get_valid_centre_test_id():
    db = SessionLocal()

    try:
        centre_test = db.scalar(select(CentreTest).limit(1))

        assert centre_test is not None

        return centre_test.id
    finally:
        db.close()


def test_create_booking():
    email, headers = create_logged_in_user()

    try:
        response = client.post(
            "/bookings/",
            headers=headers,
            json={
                "centre_test_id": get_valid_centre_test_id(),
                "appointment_at": (
                    datetime.now(timezone.utc) + timedelta(days=2)
                ).isoformat(),
            },
        )

        assert response.status_code == 201
        assert response.json()["status"] == "PENDING"
        assert response.json()["amount"] > 0
    finally:
        delete_booking_test_user(email)


def test_create_booking_requires_token():
    response = client.post(
        "/bookings/",
        json={
            "centre_test_id": get_valid_centre_test_id(),
            "appointment_at": (
                datetime.now(timezone.utc) + timedelta(days=2)
            ).isoformat(),
        },
    )

    assert response.status_code == 401


def test_create_booking_rejects_invalid_centre_test():
    email, headers = create_logged_in_user()

    try:
        response = client.post(
            "/bookings/",
            headers=headers,
            json={
                "centre_test_id": 999999,
                "appointment_at": (
                    datetime.now(timezone.utc) + timedelta(days=2)
                ).isoformat(),
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Centre test offering not found"
    finally:
        delete_booking_test_user(email)