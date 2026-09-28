from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.models.booking import Booking
from src.models.centre_offering import CentreTest
from src.models.user import User
from src.schemas.booking import BookingCreate
from src.utils.db import get_db
from src.utils.dependencies import get_current_user

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if booking_data.appointment_at.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="Appointment time must include a timezone",
        )

    if booking_data.appointment_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Appointment time must be in the future",
        )

    centre_test = (
        db.query(CentreTest)
        .filter(CentreTest.id == booking_data.centre_test_id)
        .first()
    )

    if not centre_test:
        raise HTTPException(
            status_code=404,
            detail="Centre test offering not found",
        )

    booking = Booking(
        user_id=current_user.id,
        centre_test_id=centre_test.id,
        appointment_at=booking_data.appointment_at,
        amount=centre_test.price,
        status="PENDING",
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return {
        "id": booking.id,
        "centre_test_id": booking.centre_test_id,
        "appointment_at": booking.appointment_at,
        "amount": float(booking.amount),
        "status": booking.status,
    }