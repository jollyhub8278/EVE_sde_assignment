#DTOs (Data Transfer Objects).

from pydantic import BaseModel, Field

class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=100)
    
class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=100)