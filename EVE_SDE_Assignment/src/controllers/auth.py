from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.models.user import User
from src.schemas.auth import SignupRequest
from src.utils.db import get_db
from src.utils.security import hash_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user_data: SignupRequest, db: Session = Depends(get_db)):
    name = user_data.name.strip()
    email = user_data.email.strip().lower()

    if not name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    if "@" not in email:
        raise HTTPException(status_code=400, detail="Enter a valid email address")

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    new_user = User(
        name=name,
        email=email,
        hashed_password=hash_password(user_data.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
        },
    }