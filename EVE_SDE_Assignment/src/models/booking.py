from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.db import Base


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
      CheckConstraint(
        "status IN ('PENDING', 'CONFIRMED', 'FAILED', 'CANCELLED')",
        name="ck_bookings_valid_status",
    ),
)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index = True,
    )

    centre_test_id: Mapped[int] = mapped_column(
        ForeignKey("centre_tests.id"),
        nullable=False,
        index = True,
    )

    appointment_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )