import hmac
import os
from fastapi import APIRouter, Depends,Header, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.models.booking import Booking
from src.models.payment import Payment
from src.models.user import User
from src.models.webhook_event import WebhookEvent
from src.schemas.payment import PaymentCreate, PaymentWebhook
from src.utils.db import get_db
from src.utils.dependencies import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])
WEBHOOK_SECRET = os.getenv("PAYMENT_WEBHOOK_SECRET")

@router.post("/", status_code=status.HTTP_201_CREATED)
def process_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == payment_data.booking_id)
        .with_for_update()
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot pay for another user's booking",
        )

    if booking.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="This booking cannot be paid",
        )

    payment = Payment(
        booking_id=booking.id,
        amount=booking.amount,
        status=payment_data.result,
    )

    booking.status = (
        "CONFIRMED"
        if payment_data.result == "SUCCESS"
        else "FAILED"
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)
    db.refresh(booking)

    return {
        "payment_id": payment.id,
        "booking_id": booking.id,
        "payment_status": payment.status,
        "booking_status": booking.status,
        "amount": payment.amount,
    }
    
@router.post("/webhook/")
def payment_webhook(
    webhook_data: PaymentWebhook,
    db: Session = Depends(get_db),
    provider_secret: str | None = Header(
        default=None,
        alias="X-Webhook-Secret",
    ),
):
    if not WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Payment webhook secret is not configured",
        )

    if (
        not provider_secret
        or not hmac.compare_digest(
            provider_secret,
            WEBHOOK_SECRET,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook secret",
        )
    existing_event = (
        db.query(WebhookEvent)
        .filter(WebhookEvent.event_id == webhook_data.event_id)
        .first()
    )

    if existing_event:
        if (
            existing_event.booking_id != webhook_data.booking_id
            or existing_event.result != webhook_data.result
        ):
            raise HTTPException(
                status_code=409,
                detail="Webhook event ID was already used with different data",
            )

        return {
            "message": "Webhook event already processed",
            "event_id": existing_event.event_id,
        }

    try:
        booking = (
            db.query(Booking)
            .filter(Booking.id == webhook_data.booking_id)
            .with_for_update()
            .first()
        )

        if not booking:
            raise HTTPException(
                status_code=404,
                detail="Booking not found",
            )

        if booking.status != "PENDING":
            raise HTTPException(
                status_code=409,
                detail=f"Booking is already {booking.status}",
            )

        webhook_event = WebhookEvent(
            event_id=webhook_data.event_id,
            booking_id=booking.id,
            result=webhook_data.result,
        )

        db.add(webhook_event)
        db.flush()

        payment = Payment(
            booking_id=booking.id,
            amount=booking.amount,
            status=webhook_data.result,
        )

        db.add(payment)

        booking.status = (
            "CONFIRMED"
            if webhook_data.result == "SUCCESS"
            else "FAILED"
        )

        db.commit()
        db.refresh(webhook_event)
        db.refresh(booking)

        return {
            "message": "Webhook processed successfully",
            "event_id": webhook_event.event_id,
            "booking_status": booking.status,
        }

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()

        existing_event = (
            db.query(WebhookEvent)
            .filter(WebhookEvent.event_id == webhook_data.event_id)
            .first()
        )

        if existing_event:
            return {
                "message": "Webhook event already processed",
                "event_id": existing_event.event_id,
            }

        raise