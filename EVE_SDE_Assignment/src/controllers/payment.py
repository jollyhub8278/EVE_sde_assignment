from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.models.booking import Booking
from src.models.payment import Payment
from src.models.user import User
from src.models.webhook_event import WebhookEvent
from src.schemas.payment import PaymentCreate, PaymentWebhook
from src.utils.db import get_db
from src.utils.dependencies import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def process_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == payment_data.booking_id)
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
        "amount": float(payment.amount),
    }
    
@router.post("/webhook/")
def payment_webhook(
    webhook_data: PaymentWebhook,
    db: Session = Depends(get_db),
):
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

    booking = (
        db.query(Booking)
        .filter(Booking.id == webhook_data.booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    webhook_event = WebhookEvent(
        event_id=webhook_data.event_id,
        booking_id=booking.id,
        result=webhook_data.result,
    )

    db.add(webhook_event)

    if booking.status == "PENDING":
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

    return {
        "message": "Webhook processed successfully",
        "event_id": webhook_event.event_id,
        "booking_status": booking.status,
    }