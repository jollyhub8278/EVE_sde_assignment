# EVE Diagnostics Booking API

A FastAPI and PostgreSQL backend for diagnostic-test bookings and simulated payments.

FastAPI backend for diagnostic test bookings and simulated payments.

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
    A["Login"] --> T["Select Centre and Test"]
    T --> B["Create PENDING booking"]
    B --> C["Pay or send webhook"]
    C --> D["CONFIRMED or FAILED"]
    B --> E["Cancel"]
    E --> F["CANCELLED"]
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

### 4. Create the database

```sql
CREATE DATABASE eve_diagnostics;
```

### 5. Configure environment variables

Copy `.env.example` to `.env`, then set your PostgreSQL password and secure values.

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/eve_diagnostics
TEST_DATABASE_URL=postgresql+psycopg://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/eve_diagnostics_test

JWT_SECRET=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
<<<<<<< HEAD

PAYMENT_WEBHOOK_SECRET=replace_with_a_webhook_secret
```

### 6. Run the application

=======

PAYMENT_WEBHOOK_SECRET=replace_with_a_webhook_secret
```

### 6. Run the application

>>>>>>> 55590807424f175719f5600fde6856e8e0a32943
```bash
python -m uvicorn src.main:app --reload
```

In another terminal:

>>>>>>> 55590807424f175719f5600fde6856e8e0a32943
```bash
python -m src.seed
```

Swagger UI: `http://127.0.0.1:8000/docs`

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

## Example Booking Flow

Get available offerings:

```http
GET /centres/
```

Each test `id` in this response is a `centre_test_id`. Use it to create a booking:

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

Process a payment:

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

Send a provider webhook:

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

Repeated deliveries with the same event ID do not create duplicate payments. A repeated event ID with different data returns `409 Conflict`.

## Database Design

| Table | Purpose |
|---|---|
| `users` | User profile and hashed password |
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

- Passwords are hashed with `pwdlib`
- JWT is required for user-owned resources
- Users cannot pay for or cancel another user's booking
- Appointment times must include a timezone and be in the future
- Booking price always comes from the database
- Row locks prevent duplicate concurrent payment processing
- Webhooks require `X-Webhook-Secret`
- Webhook events are idempotent using unique event IDs

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

- In this small assignment, any JWT-authenticated user can manage centre catalogue data. Production code should add admin roles.
- Payments are simulated; a real system would use provider signatures, refunds, and retry queues.
- With more time: Alembic migrations, pagination, structured logging, CI, Docker, and role-based access control.
