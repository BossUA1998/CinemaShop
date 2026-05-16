# 🎬 CinemaShop

> A production-ready async REST API for an online cinema store — featuring secure JWT auth, Stripe payments, background email notifications, and a fully containerized setup.

---

## ✨ Features

### 🔐 Authentication & Security
- **JWT access + refresh token** flow with secure rotation
- **Email activation** — account stays inactive until confirmed via link
- **Password reset** via email with expiring tokens
- **Argon2** password hashing — one of the strongest algorithms available
- Role-based access: **User**, **Moderator**, **Admin**
- **Docs protected by middleware** — `/docs` and `/redoc` require a valid JWT token

### 🎥 Movies & Discovery
- Rich movie catalog seeded from **IMDb CSV dataset** (~1000 films)
- Metadata: genre, director, cast, certification, IMDb rating, Metascore, gross
- **Advanced filtering** by genre, director, star, certification, price, rating, year
- Favorite movies — save and retrieve your personal watchlist
- **Reactions** (like/dislike) on movies with email notifications on activity
- **Comments & replies** with email notifications on answers

### 🛒 Cart & Orders
- Per-user cart with duplicate prevention
- Order creation from cart with multi-layer validation:
  - ✅ Cart is not empty
  - ✅ No already-purchased movies
  - ✅ No conflicting pending orders with the same films
  - ✅ Movie availability check
  - ✅ Price integrity verified server-side before Stripe session
- Order cancellation available before payment completes

### 💳 Payments via Stripe
- **Stripe Checkout** session creation with locked pricing
- Full webhook handling for real-time events:
  - `checkout.session.expired` → handle unpaid/abandoned sessions
  - `charge.succeeded` → capture transaction ID, send email receipt
  - `charge.refunded` → handle refunds
- **Webhook signature verification** on every incoming request
- Payment metadata passed via `payment_intent_data` for reliable tracking
- Receipt email sent automatically after successful charge

### 📧 Email Notifications (Async)
- All emails sent via **aiosmtplib** as background tasks — zero request latency
- Beautiful **HTML email templates** for:
  - Account activation request & confirmation
  - Password reset request & confirmation
  - Comment reply notifications
  - Movie reaction notifications
  - Moderator alert on movie deletion attempt

### 🔁 Background Tasks (Celery + Redis)
- **Celery worker** for heavy async jobs
- **Celery Beat** for scheduled periodic tasks
- Redis as the message broker

### 🧑‍💼 Moderator Panel
- View all orders filtered by user, date, status
- View all payments across the platform
- Manage movie catalog

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 + asyncpg |
| Migrations | Alembic |
| Validation | Pydantic v2 + BaseSettings |
| Passwords | argon2-cffi |
| Auth | python-jose (JWT, HS256) |
| Payments | Stripe |
| Email | aiosmtplib |
| Task Queue | Celery + Redis |
| Containerization | Docker + Docker Compose |
| DB Admin | pgAdmin 4 |

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Stripe CLI (for local webhook testing)

### 1. Clone the repository
```bash
git clone -b develop https://github.com/BossUA1998/CinemaShop.git
cd CinemaShop
```

### 2. Configure environment
```bash
cp .env.sample .env
```

Fill in your `.env`:
```env
# PostgreSQL
POSTGRES_DB=movies_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB_PORT=5432
POSTGRES_HOST=postgres_cinema_shop

# pgAdmin
PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=yourpassword

# JWT
SECRET_KEY_ACCESS=your_32_char_secret
SECRET_KEY_REFRESH=your_32_char_secret
JWT_SIGNING_ALGORITHM=HS256

# Email (if password has spaces, replace with |)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your|app|password

# Celery
CELERY_BROKER_URL=redis://redis:6379

# Stripe
STRIPE_PRIVATE_KEY=sk_test_...
STRIPE_WEBHOOK_KEY=whsec_...
STRIPE_SUCCESS_URL=http://localhost:8000/payments/success
STRIPE_CANCEL_URL=http://localhost:8000/payments/cancel
```

### 3. Run the project
```bash
docker compose up --build
```

This starts:
- `web` — FastAPI app on port `8000`
- `db` — PostgreSQL 16
- `migrator` — runs Alembic migrations + seeds IMDb data automatically
- `redis` — message broker
- `worker` — Celery worker
- `beat` — Celery scheduler
- `pgadmin` — database UI on port `3333`

### 4. Test Stripe webhooks locally
```bash
docker run --rm -it \
  --network cinemashop_default \
  stripe/stripe-cli:latest \
  listen --api-key sk_test_... --forward-to web:8000/payments/webhook/
```

---

## 📁 Project Structure

```
CinemaShop/
├── src/
│   ├── main.py                  # FastAPI app + middleware
│   ├── config/
│   │   ├── settings.py          # BaseSettings (Pydantic)
│   │   └── dependencies.py      # FastAPI Depends annotations
│   ├── routes/                  # API routers
│   │   ├── accounts.py
│   │   ├── movies.py
│   │   ├── cart.py
│   │   ├── orders.py
│   │   └── payments.py
│   ├── crud/                    # Async DB queries
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── database/
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── session.py           # Async session setup
│   │   ├── populate.py          # CSV seeder
│   │   ├── migrations/          # Alembic versions
│   │   └── datasets/            # imdb_movies.csv
│   ├── notifications/
│   │   ├── emails.py            # aiosmtplib email sender
│   │   └── templates/           # HTML email templates
│   ├── celery_worker/           # Celery app + tasks
│   └── security/                # JWT manager + Argon2
├── docker-compose.yaml
├── Dockerfile
├── pyproject.toml
└── .env.sample
```

---

## 🌐 API Overview

| Prefix | Description |
|---|---|
| `/auth` | Register, activate, login, logout, refresh, password reset |
| `/movies` | Browse, filter, favorite, react, comment |
| `/cart` | Add, remove, view cart items |
| `/orders` | Create, view, cancel orders |
| `/payments` | Initiate Stripe checkout, webhook handler, payment history |

Interactive docs available at `/docs` *(JWT required)*.

---

## 🧪 Test Payment

Use Stripe's test card:
```
Card number:  4242 4242 4242 4242
Expiry:       Any future date
CVC:          Any 3 digits
```

---

## 👨‍💻 Author

**Arsenii Kushnir** — [arseniykushnir2007@gmail.com](mailto:arseniykushnir2007@gmail.com)
