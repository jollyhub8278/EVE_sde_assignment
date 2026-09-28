from pydantic import BaseModel
from pydantic import Field


class AvailableTestResponse(BaseModel):
    id: int
    name: str
    price: float


class CentreResponse(BaseModel):
    id: int
    name: str
    location: str
    tests: list[AvailableTestResponse]
    
class CentreTestCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    price: float = Field(gt=0)


class CentreCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    location: str = Field(min_length=2, max_length=255)
    tests: list[CentreTestCreate] = Field(min_length=1)