# RevoShop API

REST API for the RevoShop e-commerce platform, built with Flask, SQLAlchemy, and PostgreSQL. It manages users, categories, products, orders, and order items through a RESTful interface with JWT authentication and role-based access control.

**Live API:** [https://module-2-gede-ananda.vercel.app/](https://module-2-gede-ananda.vercel.app/)

**Full endpoint documentation:** [Postman Documentation](https://documenter.getpostman.com/view/49407169/2sBYAuSAwp)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Database Design](#database-design)
- [Project Structure](#project-structure)
- [Running the Project Locally](#running-the-project-locally)
- [Deployment](#deployment)
- [Endpoints](#endpoints)
- [Authentication & Authorization](#authentication--authorization)
- [Testing](#testing)
- [Load Testing](#load-testing)
- [Design Notes](#design-notes)
- [Screenshots](#screenshots)

---

## Overview

RevoShop is a backend API for an online store that manages a categorized product catalog, user accounts, and orders. An order can contain several products at once, and a product can appear in many different orders — a many-to-many relationship bridged by the `order_items` table, which also stores the quantity and the price at the moment the transaction happened.

The API is designed as a single-store system: admins manage the catalog (categories and products), while customers browse the catalog and place orders.

The deployed instance is available at [https://module-2-gede-ananda.vercel.app/](https://module-2-gede-ananda.vercel.app/) — that base URL is the prefix for every endpoint listed below. For example:

```bash
curl https://module-2-gede-ananda.vercel.app/products
curl https://module-2-gede-ananda.vercel.app/health
```

---

## Features

**Authentication & Authorization**
- Registration and login with hashed passwords
- JWT with access tokens (30 minutes) and refresh tokens (30 days)
- Logout with token revocation through a blocklist
- Role-based access control (admin / customer)

**User Management**
- Admin-only user listing with pagination, role filter, and search by username or email
- Profile updates: a user can update their own account, an admin can update any account
- Role changes are restricted to admins, so no customer can promote themselves
- Password hashes are never included in any response

**Catalog Management**
- Full CRUD for categories and products
- Pagination, filtering (by category and active status), and product name search
- Deletion guard: a product that has already been ordered cannot be deleted
- Deletion guard: a category that still holds products cannot be deleted

**Order Management**
- Order creation with multiple products at once
- Automatic `total_amount` calculation
- Automatic stock deduction when an order is created
- Stock availability and product active status validated before an order is processed
- Duplicate items within one order are merged automatically
- Row-level locking to prevent race conditions when stock is contended
- Order cancellation with stock restored
- Customers only see their own orders; admins see all of them

**Quality & Security**
- Input validation across every endpoint with specific error messages
- Global error handler: all errors are returned as JSON with the correct status code
- Automatic rollback on database transaction failure
- Sensitive configuration kept in `.env`

---

## Tech Stack

| Category | Technology |
|---|---|
| Framework | Flask |
| ORM | SQLAlchemy (Flask-SQLAlchemy) |
| Migrations | Flask-Migrate (Alembic) |
| Database | PostgreSQL (Supabase in production) |
| Authentication | Flask-JWT-Extended |
| Configuration | python-dotenv |
| Testing | pytest |
| Load Testing | Locust |
| Hosting | Vercel |
| Database GUI | pgAdmin |

---

## Database Design

Five core tables with the following relationships:

- **users** → **orders** (one-to-many): one user can have many orders
- **categories** → **products** (one-to-many): one category holds many products
- **orders** ↔ **products** (many-to-many via **order_items**): one order contains many products, one product appears in many orders

An additional **token_blocklist** table stores the JWT ID (`jti`) of tokens revoked at logout.

### Referential Integrity Rules

| Relationship | ON DELETE | Reason |
|---|---|---|
| `order_items` → `orders` | CASCADE | An item is meaningless without its order |
| `order_items` → `products` | RESTRICT | Keeps transaction history intact |
| `products` → `categories` | RESTRICT | Prevents a product from losing its category |
| `orders` → `users` | RESTRICT | Keeps order history tied to its owner |

Product prices are copied into `order_items.price` when an order is created rather than referenced. This guarantees that future price changes do not rewrite the value of transactions that already happened.

---

## Project Structure

```
revoshop-api/
├── app/
│   ├── __init__.py          # application factory
│   ├── config.py            # configuration (Config, TestConfig)
│   ├── extensions.py        # db, migrate, jwt, cors instances
│   ├── models/
│   │   ├── user.py          # User
│   │   ├── product.py       # Category, Product
│   │   ├── order.py         # Order, OrderItem
│   │   └── token.py         # TokenBlocklist
│   ├── routes/
│   │   ├── auth.py          # register, login, refresh, logout, me
│   │   ├── users.py         # list users, update user
│   │   ├── categories.py    # CRUD categories
│   │   ├── products.py      # CRUD products
│   │   └── orders.py        # order, cancel, status
│   └── utils/
│       ├── decorators.py    # role_required
│       └── errors.py        # global error handlers
├── migrations/              # Alembic migration files
├── tests/
│   ├── conftest.py          # fixtures
│   ├── test_auth.py
│   ├── test_categories.py
│   ├── test_products.py
│   └── test_orders.py
├── .env.example
├── .gitignore
├── locustfile.py
├── requirements.txt         # runtime dependencies (installed by Vercel)
├── requirements-dev.txt     # test and load-test tooling
├── run.py                   # local development entrypoint
└── wsgi.py                  # WSGI entrypoint used in production
```

---

## Running the Project Locally

### Prerequisites

- Python 3.10+
- PostgreSQL

### 1. Clone the repository

```bash
git clone https://github.com/Revou-FSSE-Jun26/module-2-GedeAnanda.git
cd module-2-GedeAnanda
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # needed to run the tests
```

### 4. Create the databases

Through pgAdmin or psql, create two databases:

```sql
CREATE DATABASE revoshop_db;
CREATE DATABASE revoshop_test;
```

### 5. Configure the environment

Copy `.env.example` to `.env`, then fill in the values:

```bash
cp .env.example .env
```

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/revoshop_db
TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/revoshop_test
SECRET_KEY=<random string>
JWT_SECRET_KEY=<a different random string>
CORS_ORIGINS=*
```

Generate a secret key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 6. Run the migrations

```bash
export FLASK_APP=run.py          # Windows: set FLASK_APP=run.py
flask db upgrade
```

### 7. Start the application

```bash
flask run
```

The API runs at `http://127.0.0.1:5000`.

### 8. Creating an admin account

POST, PUT, and DELETE endpoints for products and categories require the `admin` role, as does `GET /users`. Public registration always produces a `customer` — that is deliberate, so there is no path to self-assign as admin.

Register a user through the API, then promote them in the database:

```sql
UPDATE users SET role = 'admin' WHERE email = 'your_email@example.com';
```

Log in again afterwards so the new token carries the admin role. Once one admin exists, further role changes can be made through `PUT /users/<id>`.

---

## Deployment

The API is deployed on Vercel at [https://module-2-gede-ananda.vercel.app/](https://module-2-gede-ananda.vercel.app/), backed by a Supabase PostgreSQL database.

- Vercel's Python runtime imports `wsgi.py` and serves the WSGI callable named `app`. The file is deliberately not called `app.py`, which would shadow the `app/` package it imports from.
- `requirements.txt` holds runtime dependencies only; test and load-test tooling lives in `requirements-dev.txt` so it is never installed at build time.
- Two Supabase connection strings are used for different jobs: the **transaction pooler** (port 6543) at runtime, which suits serverless, and the **session pooler** (port 5432) for running `flask db upgrade` locally, because the transaction pooler cannot run the DDL transactions Alembic needs.
- `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`, and `CORS_ORIGINS` are set as Vercel environment variables. Set `CORS_ORIGINS` to your frontend origin once you have one instead of leaving it as `*`.

Migrations are not run automatically on deploy — apply them locally against the session pooler before shipping schema changes.

---

## Endpoints

Full documentation with request and response examples is available in the [Postman Documentation](https://documenter.getpostman.com/view/49407169/2sBYAuSAwp). Every path below is relative to `https://module-2-gede-ananda.vercel.app/` in production, or `http://127.0.0.1:5000` locally.

### Service

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/` | Public | Service name and status |
| GET | `/health` | Public | Health check |

### Auth

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/auth/register` | Public | Register a new user |
| POST | `/auth/login` | Public | Log in, returns access & refresh tokens |
| POST | `/auth/refresh` | Refresh token | Exchange a refresh token for a new access token |
| POST | `/auth/logout` | Authenticated | Revoke the current access token |
| GET | `/auth/me` | Authenticated | The currently logged-in user |

### Users

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/users` | Admin | List all users with pagination, role filter, and search |
| PUT | `/users/<id>` | Owner or admin | Update a user's username, email, password, or role |

Query parameters for `GET /users`: `page`, `per_page` (capped at 100), `role`, `search` (matches username or email).

`PUT /users/<id>` accepts a partial body — only the fields present are updated:

```json
{
  "username": "new name",
  "email": "new@example.com",
  "password": "at-least-8-chars",
  "role": "admin"
}
```

Rules enforced by this endpoint:

- A customer may only update their own account; an admin may update anyone.
- `role` may only be changed by an admin, and must be `customer` or `admin`. A customer attempting it gets 403.
- `email` must remain unique — a collision with another account returns 409.
- `password` must be at least 8 characters and is stored hashed, matching registration.

### Categories

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/categories` | Public | List all categories |
| GET | `/categories/<id>` | Public | Category detail with its products |
| POST | `/categories` | Admin | Create a category |
| PUT | `/categories/<id>` | Admin | Update a category |
| DELETE | `/categories/<id>` | Admin | Delete a category (rejected if products remain) |

### Products

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/products` | Public | List products with pagination, filtering, and search |
| GET | `/products/<id>` | Public | Single product detail |
| POST | `/products` | Admin | Create a product |
| PUT | `/products/<id>` | Admin | Update a product |
| DELETE | `/products/<id>` | Admin | Delete a product (rejected if already ordered) |

Query parameters for `GET /products`: `page`, `per_page`, `category_id`, `is_active`, `search`.

### Orders

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/orders` | Authenticated | The user's own orders (admins see all) |
| GET | `/orders/<id>` | Authenticated | Order detail with its items and products |
| POST | `/orders` | Authenticated | Create an order |
| PUT | `/orders/<id>/status` | Admin | Change an order's status |
| POST | `/orders/<id>/cancel` | Authenticated | Cancel an order and restore stock |

Valid statuses: `pending`, `paid`, `shipped`, `completed`, `cancelled`.

### Response Format

Success response:

```json
{
  "message": "Products retrieved successfully",
  "data": [ ... ],
  "pagination": { ... }
}
```

Error response:

```json
{
  "error": "Product not found"
}
```

---

## Authentication & Authorization

The API uses JWT with an access token / refresh token pattern.

**Access tokens** (30 minutes) are sent with every request that requires authentication:

```
Authorization: Bearer <access_token>
```

**Refresh tokens** (30 days) are used only on `POST /auth/refresh` to obtain a new access token without logging in again.

**Token revocation.** JWTs are stateless — a token stays valid until it expires, even after the user logs out. To handle that, `POST /auth/logout` stores the token's `jti` (JWT ID) in the `token_blocklist` table. Every authenticated request checks the blocklist before proceeding, so a logged-out token is rejected immediately.

**Roles.** A user's role is embedded as a custom claim inside the token, so authorization checks do not need a database query on every request. The trade-off: a role change only takes effect once the old token expires or the user logs in again — including a role change made through `PUT /users/<id>`.

---

## Testing

The test suite covers authentication, categories, products, and orders, with both happy paths and error cases for each endpoint.

```bash
pytest -v
```

Tests run against a separate database (`TEST_DATABASE_URL`). Each test starts from an empty database — tables are created before and dropped after — so tests do not affect each other and can run in any order.

PostgreSQL is used for testing rather than SQLite so the behavior under test matches production exactly — in particular row-level locking, foreign key constraints, case-insensitive search, and fixed-precision numeric types.

Running a single file:

```bash
pytest tests/test_orders.py -v
```

---

## Load Testing

```bash
flask run                    # terminal 1
locust                       # terminal 2
```

Open `http://localhost:8089` and set the host to `http://127.0.0.1:5000`.

The scenario simulates a user journey: register, browse the product list, open a product detail, place an order, then view the order just created.

Results at 200 concurrent users: 386 RPS, 0% failures, median response time 2–5 ms, 95th percentile under 20 ms.

In a test with limited stock, the system returned 409 Conflict for orders exceeding availability without a single stock value going negative — confirming that row-level locking holds under real load.

---

## Design Notes

Several decisions deviate from the original specification, each made deliberately:

**Orders are cancelled, not deleted.** An order is a transaction record needed for history and auditing. `POST /orders/<id>/cancel` sets the status to `cancelled` and restores stock instead of deleting the row along with all its order items. Only `pending` orders can be cancelled — an order already paid or shipped needs a refund or return process, not a column update.

**Order edits are limited to status.** Changing an order's contents means recalculating the stock delta per item and risks producing inconsistent state. `PUT /orders/<id>/status` only changes the status; to change contents, cancel the order and create a new one.

**Registration lives under `/auth`.** `POST /auth/register` is grouped with the other authentication endpoints for consistency rather than standing alone as `POST /users`. The `/users` resource is reserved for administration and profile updates.

**JWT for authentication.** The specification lists JWT as optional and allows passing `user_id` in the request body. That approach was not adopted because it lets anyone claim to be another user. JWT was chosen so identity comes from a signed token rather than manipulable input.

**Centralized error handling.** Instead of repeating `try/except` blocks in every route, database errors and unexpected exceptions are handled in a global error handler. Every failure rolls back the session, logs details server-side, and returns a safe JSON response to the client.

---

## Screenshots

Test evidence and database structure are in the `img/` folder:

- Postman requests for each HTTP method (GET, POST, PUT, DELETE)
- Table structure and relationships in pgAdmin
- ERD diagram
- Locust dashboard at 200 concurrent users

---

## Author

I Gede Ananda Bela Persada — RevoU Software Engineering
