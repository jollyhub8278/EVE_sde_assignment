# EVE Diagnostics Booking API

A backend service for diagnostic-test bookings and simulated payments, built with FastAPI and PostgreSQL.

It supports user authentication with JWT, diagnostic-centre and test management, protected bookings, simulated payments, and idempotent payment webhooks.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- PyJWT
- pwdlib for password hashing
- Pytest and HTTPX for tests

## Features

- User signup and login
- JWT-based protected routes
- Input validation using Pydantic schemas
- Retrieve diagnostic centres, tests, and prices
- Add diagnostic centres and their available tests
- Create a diagnostic-test booking
- View the logged-in user's bookings
- Simulate successful or failed payments
- Process idempotent payment webhooks
- Automated tests for major success and error cases

## Project Structure

```text
src/
├── controllers/       # API routes and business logic
├── models/            # SQLAlchemy database models
├── schemas/           # Request and response validation schemas
├── utils/             # Database, JWT, and dependency helpers
├── main.py            # FastAPI application entry point
└── seed.py            # Sample diagnostic catalogue data

tests/                 # Automated tests
requirements.txt
README.md
```

## Booking and Payment Flow

```mermaid
flowchart TD
    A["Sign up or log in"] --> B["Create protected booking"]
    B --> C["Booking status: PENDING"]
    C --> D["Payment endpoint or webhook"]
    D --> E["Payment record created"]
    E --> F["Booking: CONFIRMED or FAILED"]
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/jollyhub8278/EVE_sde_assignment.git
cd EVE_SDE_Assignment
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv env
.\env\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Create the PostgreSQL database

Using pgAdmin or PostgreSQL terminal, create:

```sql
CREATE DATABASE eve_diagnostics;
```

### 5. Create a `.env` file

Create `.env` in the project root:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/eve_diagnostics

JWT_SECRET=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

Replace `YOUR_POSTGRES_PASSWORD` with your local PostgreSQL password.

### 6. Run the application

Run this command from the folder that contains `src`:

```powershell
python -m uvicorn src.main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

Interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

### 7. Seed sample diagnostic data

Open a second terminal in the project folder and run:

```powershell
python -m src.seed
```

This creates sample centres, diagnostic tests, and centre-test offerings.

## API Endpoints

| Method | Endpoint | Authentication | Description |
|---|---|---:|---|
| POST | `/auth/signup` | No | Register a new user |
| POST | `/auth/login` | No | Log in and receive a JWT token |
| GET | `/auth/me` | Yes | Get the current user's profile |
| GET | `/centres/` | No | Retrieve diagnostic centres, tests, and prices |
| POST | `/centres/` | Yes | Add a diagnostic centre with available tests |
| POST | `/bookings/` | Yes | Create a diagnostic-test booking |
| GET | `/bookings/me/` | Yes | Get bookings belonging to the current user |
| POST | `/payments/` | Yes | Simulate payment processing |
| POST | `/payments/webhook/` | No* | Process payment-provider webhook events |
| GET | `/health` | No | Health-check endpoint |
| GET | `/db-check` | No | Verify database connectivity |

\*The webhook is intentionally public because it simulates an external payment provider.

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

Copy the returned `access_token` and use it as:

```text
Authorization: Bearer <access_token>
```

### Get Centres and Available Tests

```http
GET /centres/
```

The response includes each centre, its location, offered tests, and prices. Use a `centre_test_id` from this response when creating a booking.

### Add a Diagnostic Centre

```http
POST /centres/
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "name": "CarePlus Diagnostics",
  "location": "Jaipur, Rajasthan",
  "tests": [
    {
      "name": "Vitamin D",
      "price": 750
    },
    {
      "name": "Lipid Profile",
      "price": 550
    }
  ]
}
```

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

A new booking is created with:

```text
status = PENDING
```

The amount is copied from the centre-test offering, so the client cannot change the price.

### Simulate a Payment

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

Possible payment results:

```text
SUCCESS
FAILED
```

A successful payment changes the booking to `CONFIRMED`. A failed payment changes it to `FAILED`.

### Payment Webhook

```http
POST /payments/webhook/
Content-Type: application/json
```

```json
{
  "event_id": "event_001",
  "booking_id": 1,
  "result": "SUCCESS"
}
```

Sending the same `event_id` again returns:

```json
{
  "message": "Webhook event already processed",
  "event_id": "event_001"
}
```

This prevents duplicate payment records and duplicate booking updates.

## Database Design

| Table | Purpose |
|---|---|
| `users` | Stores registered users and hashed passwords |
| `centres` | Stores diagnostic-centre name and location |
| `diagnostic_tests` | Stores reusable diagnostic-test names |
| `centre_tests` | Connects a centre to a test and stores its price |
| `bookings` | Stores user booking, appointment time, amount, and status |
| `payments` | Stores simulated payment attempts and results |
| `webhook_events` | Stores unique webhook event IDs for idempotency |

### Relationships

```text
User → Bookings
Centre → Centre Tests
Diagnostic Test → Centre Tests
Centre Test → Bookings
Booking → Payments
Booking → Webhook Events
```

## Validation and Edge Cases Handled

- Duplicate signup email returns an error
- Invalid login credentials return `401 Unauthorized`
- Protected endpoints require a valid JWT
- A user cannot pay for another user's booking
- Invalid booking IDs return `404 Not Found`
- A booking must use a valid centre-test offering
- Appointment time must include a timezone and be in the future
- Booking amount comes from the database price, not the request body
- A non-pending booking cannot be paid again
- Duplicate centre creation returns `409 Conflict`
- Repeated webhook events do not create duplicate payment records
- Failed payments update the booking status to `FAILED`

## Running Tests

Run all tests with:

```powershell
python -m pytest
```

Current result:

```text
25 passed
```

## Assumptions

- This is a compact backend assignment, so any authenticated user can add diagnostic catalogue data. In a production system, this endpoint should be restricted to an admin role.
- Diagnostic-test names are shared across centres; each centre can set its own price through `centre_tests`.
- Payment processing is deterministic for testing: the client sends `SUCCESS` or `FAILED`.
- The webhook endpoint does not require JWT because it represents an external provider callback.
- Webhook idempotency is implemented using a unique `event_id`.
- No real payment gateway or webhook signature verification is included because payments are simulated.

## Improvements With More Time

- Add role-based access control for catalogue management
- Use Alembic migrations instead of creating tables at startup
- Add webhook signature verification
- Add pagination and filtering for centres and bookings
- Add cancellation endpoint and cancellation rules
- Add booking-slot availability checks
- Add structured logging and request IDs
- Add Docker and Docker Compose for one-command setup
- Add CI pipeline to run tests automatically on GitHub
- Add rate limiting and retry handling for webhook delivery
