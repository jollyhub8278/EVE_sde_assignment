from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.models.booking import Booking
from src.models.centre_offering import CentreTest
from src.models.user import User
from src.schemas.booking import BookingCreate, BookingResponse
from src.utils.db import get_db
from src.models.centre import Centre
from src.models.diagnostic import DiagnosticTest
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
        "amount": booking.amount,
        "status": booking.status,
    }
    
@router.get("/me/", response_model=list[BookingResponse])
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Booking, Centre, DiagnosticTest)
        .join(
            CentreTest,
            Booking.centre_test_id == CentreTest.id,
        )
        .join(Centre, CentreTest.centre_id == Centre.id)
        .join(
            DiagnosticTest,
            CentreTest.test_id == DiagnosticTest.id,
        )
        .filter(Booking.user_id == current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )

    return [
        {
            "id": booking.id,
            "centre_name": centre.name,
            "centre_location": centre.location,
            "test_name": diagnostic_test.name,
            "appointment_at": booking.appointment_at,
            "amount": booking.amount,
            "status": booking.status,
        }
        for booking, centre, diagnostic_test in rows
    ]
    
@router.post("/{booking_id}/cancel/")
def cancel_booking(booking_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user),):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
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
            detail="You cannot cancel another user's booking",
        )

    if booking.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Only pending bookings can be cancelled",
        )

    booking.status = "CANCELLED"

    db.commit()
    db.refresh(booking)

    return {
        "id": booking.id,
        "status": booking.status,
    }