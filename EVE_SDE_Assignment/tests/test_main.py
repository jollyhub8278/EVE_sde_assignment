from sqlalchemy import inspect
from src.utils.db import engine
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "EVE Diagnostics API is running"
    }


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_connection():
    response = client.get("/db-check")

    assert response.status_code == 200
    assert response.json() == {"database": "connected"}
    
def test_users_table_exists():
    table_names = inspect(engine).get_table_names()

    assert "users" in table_names
    
def test_diagnostic_tables_exist():
    table_names = inspect(engine).get_table_names()

    assert "centres" in table_names
    assert "diagnostic_tests" in table_names
    assert "centre_tests" in table_names
    
def test_bookings_table_exists():
    table_names = inspect(engine).get_table_names()

    assert "bookings" in table_names
    
def test_payments_table_exists():
    table_names = inspect(engine).get_table_names()

    assert "payments" in table_names
    
def test_webhook_events_table_exists():
    table_names = inspect(engine).get_table_names()

    assert "webhook_events" in table_names