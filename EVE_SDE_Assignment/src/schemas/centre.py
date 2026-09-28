from pydantic import BaseModel


class AvailableTestResponse(BaseModel):
    id: int
    name: str
    price: float


class CentreResponse(BaseModel):
    id: int
    name: str
    location: str
    tests: list[AvailableTestResponse]