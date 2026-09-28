from typing import Literal

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    booking_id: int = Field(gt=0)
    result: Literal["SUCCESS", "FAILED"]
    
class PaymentWebhook(BaseModel):
    event_id: str = Field(min_length=1, max_length=100)
    booking_id: int = Field(gt=0)
    result: Literal["SUCCESS", "FAILED"]