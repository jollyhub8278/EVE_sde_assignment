from decimal import Decimal

from pydantic import BaseModel, Field


class AvailableTestResponse(BaseModel):
    id: int
    name: str
    price: Decimal


class CentreResponse(BaseModel):
    id: int
    name: str
    location: str
    tests: list[AvailableTestResponse]


class CentreTestCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    price: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )


class CentreCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    location: str = Field(min_length=2, max_length=255)
    tests: list[CentreTestCreate] = Field(min_length=1)