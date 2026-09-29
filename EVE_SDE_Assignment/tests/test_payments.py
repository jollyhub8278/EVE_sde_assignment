import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import select

from src.main import app
from src.models.booking import Booking
from src.models.centre_offering import CentreTest
from src.models.payment import Payment
from src.models.user import User
from src.utils.db import SessionLocal
from src.models.webhook_event import WebhookEvent

client = TestClient(app)

WEBHOOK_HEADERS = {
    "X-Webhook-Secret": os.environ["PAYMENT_WEBHOOK_SECRET"],
}

def create_pending_booking():
    email = f"payment_{uuid4().hex}@example.com"

    client.post(
        "/auth/signup",
        json={
            "name": "Payment Test User",
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

    headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        )
    }

    db = SessionLocal()

    try:
        centre_test = db.scalar(select(CentreTest).limit(1))
        assert centre_test is not None
        centre_test_id = centre_test.id
    finally:
        db.close()

    booking_response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "centre_test_id": centre_test_id,
            "appointment_at": (
                datetime.now(timezone.utc) + timedelta(days=2)
            ).isoformat(),
        },
    )

    assert booking_response.status_code == 201

    return email, headers, booking_response.json()["id"]


def delete_payment_test_user(email: str):
    db = SessionLocal()

    try:
        user = db.scalar(select(User).where(User.email == email))

        if user:
            booking_ids = db.scalars(
                select(Booking.id).where(Booking.user_id == user.id)
            ).all()

            if booking_ids:
                db.query(WebhookEvent).filter(
                    WebhookEvent.booking_id.in_(booking_ids)
                ).delete(synchronize_session=False)
                
                db.query(Payment).filter(
                    Payment.booking_id.in_(booking_ids)
                ).delete(synchronize_session=False)

                db.query(Booking).filter(
                    Booking.id.in_(booking_ids)
                ).delete(synchronize_session=False)
                

            db.delete(user)
            db.commit()
    finally:
        db.close()


def test_successful_payment_confirms_booking():
    email, headers, booking_id = create_pending_booking()

    try:
        response = client.post(
            "/payments/",
            headers=headers,
            json={
                "booking_id": booking_id,
                "result": "SUCCESS",
            },
        )

        assert response.status_code == 201
        assert response.json()["payment_status"] == "SUCCESS"
        assert response.json()["booking_status"] == "CONFIRMED"
    finally:
        delete_payment_test_user(email)


def test_failed_payment_marks_booking_as_failed():
    email, headers, booking_id = create_pending_booking()

    try:
        response = client.post(
            "/payments/",
            headers=headers,
            json={
                "booking_id": booking_id,
                "result": "FAILED",
            },
        )

        assert response.status_code == 201
        assert response.json()["payment_status"] == "FAILED"
        assert response.json()["booking_status"] == "FAILED"
    finally:
        delete_payment_test_user(email)


def test_payment_rejects_invalid_booking_id():
    email, headers, _ = create_pending_booking()

    try:
        response = client.post(
            "/payments/",
            headers=headers,
            json={
                "booking_id": 999999,
                "result": "SUCCESS",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Booking not found"
    finally:
        delete_payment_test_user(email)
        
def test_webhook_is_idempotent():
    email, _, booking_id = create_pending_booking()
    event_id = f"event_{uuid4().hex}"

    try:
        payload = {
            "event_id": event_id,
            "booking_id": booking_id,
            "result": "SUCCESS",
        }

        first_response = client.post(
            "/payments/webhook/",
            headers=WEBHOOK_HEADERS,
            json=payload,
        )

        second_response = client.post(
            "/payments/webhook/",
            headers=WEBHOOK_HEADERS,
            json=payload,
        )

        assert first_response.status_code == 200
        assert first_response.json()["booking_status"] == "CONFIRMED"

        assert second_response.status_code == 200
        assert (
            second_response.json()["message"]
            == "Webhook event already processed"
        )

        db = SessionLocal()

        try:
            payment_count = (
                db.query(Payment)
                .filter(Payment.booking_id == booking_id)
                .count()
            )

            event_count = (
                db.query(WebhookEvent)
                .filter(WebhookEvent.event_id == event_id)
                .count()
            )

            assert payment_count == 1
            assert event_count == 1
        finally:
            db.close()
    finally:
        delete_payment_test_user(email)
        
def test_webhook_rejects_same_event_with_different_data():
    email, _, booking_id = create_pending_booking()
    event_id = f"event_{uuid4().hex}"

    try:
        first_response = client.post(
            "/payments/webhook/",
            headers=WEBHOOK_HEADERS,
            json={
                "event_id": event_id,
                "booking_id": booking_id,
                "result": "SUCCESS",
            },
        )

        conflict_response = client.post(
            "/payments/webhook/",
            headers=WEBHOOK_HEADERS,
            json={
                "event_id": event_id,
                "booking_id": booking_id,
                "result": "FAILED",
            },
        )

        assert first_response.status_code == 200

        assert conflict_response.status_code == 409
        assert (
            conflict_response.json()["detail"]
            == "Webhook event ID was already used with different data"
        )
    finally:
        delete_payment_test_user(email)
        
def test_webhook_rejects_event_for_completed_booking():
    email, _, booking_id = create_pending_booking()

    try:
        first_response = client.post(
            "/payments/webhook/",
            headers=WEBHOOK_HEADERS,
            json={
                "event_id": f"event_{uuid4().hex}",
                "booking_id": booking_id,
                "result": "SUCCESS",
            },
        )

        late_response = client.post(
            "/payments/webhook/",
            headers=WEBHOOK_HEADERS,
            json={
                "event_id": f"event_{uuid4().hex}",
                "booking_id": booking_id,
                "result": "FAILED",
            },
        )

        assert first_response.status_code == 200

        assert late_response.status_code == 409
        assert late_response.json()["detail"] == "Booking is already CONFIRMED"
    finally:
        delete_payment_test_user(email)
        
def test_user_cannot_pay_for_another_users_booking():
    owner_email, _, booking_id = create_pending_booking()
    other_email = f"other_{uuid4().hex}@example.com"

    try:
        client.post(
            "/auth/signup",
            json={
                "name": "Other User",
                "email": other_email,
                "password": "password123",
            },
        )

        login_response = client.post(
            "/auth/login",
            json={
                "email": other_email,
                "password": "password123",
            },
        )

        other_headers = {
            "Authorization": (
                f"Bearer {login_response.json()['access_token']}"
            )
        }

        response = client.post(
            "/payments/",
            headers=other_headers,
            json={
                "booking_id": booking_id,
                "result": "SUCCESS",
            },
        )

        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "You cannot pay for another user's booking"
        )
    finally:
        delete_payment_test_user(owner_email)
        delete_payment_test_user(other_email)
        
def test_payment_rejects_already_paid_booking():
    email, headers, booking_id = create_pending_booking()

    try:
        first_response = client.post(
            "/payments/",
            headers=headers,
            json={
                "booking_id": booking_id,
                "result": "SUCCESS",
            },
        )

        second_response = client.post(
            "/payments/",
            headers=headers,
            json={
                "booking_id": booking_id,
                "result": "SUCCESS",
            },
        )

        assert first_response.status_code == 201

        assert second_response.status_code == 400
        assert (
            second_response.json()["detail"]
            == "This booking cannot be paid"
        )

        db = SessionLocal()

        try:
            payment_count = (
                db.query(Payment)
                .filter(Payment.booking_id == booking_id)
                .count()
            )

            assert payment_count == 1
        finally:
            db.close()

    finally:
        delete_payment_test_user(email)
        
def test_webhook_rejects_missing_secret():
    email, _, booking_id = create_pending_booking()

    try:
        response = client.post(
            "/payments/webhook/",
            json={
                "event_id": f"event_{uuid4().hex}",
                "booking_id": booking_id,
                "result": "SUCCESS",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid webhook secret"
    finally:
        delete_payment_test_user(email)