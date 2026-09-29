import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

TESTING = os.getenv("TESTING") == "1"

DATABASE_URL = (
    os.getenv("TEST_DATABASE_URL")
    if TESTING
    else os.getenv("DATABASE_URL")
)

if not DATABASE_URL:
    environment_name = (
        "TEST_DATABASE_URL"
        if TESTING
        else "DATABASE_URL"
    )
    raise ValueError(f"{environment_name} is not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()