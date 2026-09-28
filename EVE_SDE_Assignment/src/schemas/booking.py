from datetime import datetime

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    centre_test_id: int = Field(gt=0)
    appointment_at: datetime