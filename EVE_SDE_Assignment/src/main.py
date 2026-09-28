from fastapi import FastAPI
from sqlalchemy import text

import src.models
from src.controllers.auth import router as auth_router
from src.controllers.centre import router as centre_router
from src.controllers.booking import router as booking_router
from src.utils.db import Base, engine
from src.controllers.payment import router as payment_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth_router)
app.include_router(booking_router)
app.include_router(payment_router)
app.include_router(centre_router)

@app.get("/")
def home():
    return {"message": "EVE Diagnostics API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-check")
def db_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"database": "connected"}