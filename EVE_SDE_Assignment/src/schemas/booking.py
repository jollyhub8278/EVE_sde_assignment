from datetime import datetime

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    centre_test_id: int = Field(gt=0)
    appointment_at: datetime
    
class BookingResponse(BaseModel):
    id: int
    centre_name: str
    centre_location: str
    test_name: str
    appointment_at: datetime
    amount: float
    status: str