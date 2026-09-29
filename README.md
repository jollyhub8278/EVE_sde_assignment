# EVE Diagnostics Booking API

A FastAPI and PostgreSQL backend for diagnostic-test bookings and simulated payments.

It includes JWT authentication, diagnostic-centre catalogue management, protected bookings, payment simulation, and idempotent payment webhooks.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- PyJWT
- pwdlib
- Pytest

## Features

- User signup, login, and JWT-protected routes
- Diagnostic centres, tests, and test prices
- Create and view user-owned bookings
- Cancel pending bookings
- Simulated successful and failed payments
- Idempotent payment webhook processing
- Webhook shared-secret validation
- PostgreSQL constraints for valid and duplicate data
- Isolated PostgreSQL test database

## Project Structure

```text
EVE_SDE_Assignment/
├── src/
│   ├── controllers/   # API routes
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic request/response schemas
│   ├── utils/         # Database and authentication helpers
│   ├── main.py        # FastAPI application
│   └── seed.py        # Sample catalogue data
├── tests/             # Automated tests and fixtures
├── .env.example
└── requirements.txt
```

## Booking Flow

```mermaid
flowchart TD
    A["Sign up or log in"] --> B["Select centre-test offering"]
    B --> C["Create PENDING booking"]
    C --> D["Payment or webhook"]
    D --> E["CONFIRMED or FAILED"]
    C --> F["Cancel booking"]
    F --> G["CANCELLED"]
```

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/jollyhub8278/EVE_sde_assignment.git
cd EVE_sde_assignment/EVE_SDE_Assignment
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv env
.\env\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv env
source env/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create PostgreSQL databases

Run these queries while connected to PostgreSQL:

```sql
CREATE DATABASE eve_diagnostics;
CREATE DATABASE eve_diagnostics_test;
```

- `eve_diagnostics` is used when running the application.
- `eve_diagnostics_test` is used only by pytest.

### 5. Configure environment variables

Copy `.env.example` to `.env`, then add your PostgreSQL password and secure secrets.

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/eve_diagnostics
TEST_DATABASE_URL=postgresql+psycopg://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/eve_diagnostics_test

JWT_SECRET=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

PAYMENT_WEBHOOK_SECRET=replace_with_a_webhook_secret
```

### 6. Run the application

```bash
python -m uvicorn src.main:app --reload
```

The API runs at:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

### 7. Seed sample diagnostic data

In a second terminal:

```bash
python -m src.seed
```

## API Endpoints

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| POST | `/auth/signup` | No | Register a user |
| POST | `/auth/login` | No | Log in and receive a JWT |
| GET | `/auth/me` | JWT | Get current user profile |
| GET | `/centres/` | No | List centres, test offerings, and prices |
| POST | `/centres/` | JWT | Create a centre with test offerings |
| POST | `/bookings/` | JWT | Create a pending booking |
| GET | `/bookings/me/` | JWT | List current user bookings |
| POST | `/bookings/{booking_id}/cancel/` | JWT | Cancel a pending booking |
| POST | `/payments/` | JWT | Process a simulated payment |
| POST | `/payments/webhook/` | Webhook secret | Process a payment-provider webhook |
| GET | `/health` | No | Health check |

## Example Requests

### Signup

```http
POST /auth/signup
Content-Type: application/json
```

```json
{
  "name": "Bharti Jangir",
  "email": "bharti@example.com",
  "password": "Password@123"
}
```

### Login

```http
POST /auth/login
Content-Type: application/json
```

```json
{
  "email": "bharti@example.com",
  "password": "Password@123"
}
```

Use the returned token in protected requests:

```text
Authorization: Bearer <access_token>
```

### Get Available Test Offerings

```http
GET /centres/
```

Each test object in the response contains an `id`. This is the `centre_test_id` used to create a booking.

### Create a Booking

```http
POST /bookings/
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "centre_test_id": 1,
  "appointment_at": "2027-01-15T10:30:00+05:30"
}
```

The booking starts with `PENDING` status. The price is always taken from the database, not from the request.

### Process a Payment

```http
POST /payments/
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "booking_id": 1,
  "result": "SUCCESS"
}
```

Valid payment results:

```text
SUCCESS
FAILED
```

A successful payment changes the booking to `CONFIRMED`. A failed payment changes it to `FAILED`.

### Payment Webhook

```http
POST /payments/webhook/
X-Webhook-Secret: <PAYMENT_WEBHOOK_SECRET>
Content-Type: application/json
```

```json
{
  "event_id": "event_001",
  "booking_id": 1,
  "result": "SUCCESS"
}
```

Sending the same event ID with the same payload is safe and does not create a duplicate payment. Reusing an event ID with different data returns `409 Conflict`.

## Database Design

| Table | Purpose |
|---|---|
| `users` | Registered users and hashed passwords |
| `centres` | Diagnostic-centre name and location |
| `diagnostic_tests` | Reusable diagnostic-test names |
| `centre_tests` | A test offering at a centre and its price |
| `bookings` | User appointment, copied amount, and status |
| `payments` | One simulated payment per booking |
| `webhook_events` | Processed webhook event IDs |

Important database constraints:

- Unique centre name and location
- Unique test offering per centre
- One payment per booking
- Valid booking statuses: `PENDING`, `CONFIRMED`, `FAILED`, `CANCELLED`
- Money stored as `Numeric(10, 2)`

## Validation and Security

- Passwords are hashed.
- JWT is required for user-owned booking and payment actions.
- Users cannot pay for or cancel another user’s booking.
- Appointment times must include a timezone and be in the future.
- Booking amounts come from the database.
- Row locks prevent concurrent duplicate payment processing.
- Webhooks require `X-Webhook-Secret`.
- Webhook events use unique event IDs for idempotency.
- GitHub Actions also runs the test suite automatically on every push to `main`.

## Tests

Run all tests with:

```bash
python -m pytest
```

The test suite uses `eve_diagnostics_test`, not the development database. `tests/conftest.py` recreates and seeds the test database before each test.

Current result:

```text
31 passed
```

## Assumptions and Future Improvements

- Any authenticated user can manage the diagnostic catalogue in this assignment. A production system should use admin roles.
- Payments are simulated. A production system would use provider signatures, retry logic, refunds, and reconciliation.
- With more time, I would add Alembic migrations, payment retries for failed bookings, pagination, structured logging, CI, Docker, and role-based access control.
