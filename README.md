# Smart Accounts Management

Smart Accounts Management is a Django-based financial tracking platform that helps individuals and teams manage income and expenses, upload receipts/invoices, extract data with OCR, and enforce subscription-based monthly usage limits.

## 📌 Project Overview

![Light Mode Mockup](static/images/all_devices.png)

## Table of Contents

1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Technology Stack](#technology-stack)
4. [Architecture and Modules](#architecture-and-modules)
5. [Installation and Local Setup](#installation-and-local-setup)
6. [Environment Variables](#environment-variables)
7. [User Flow](#user-flow)
8. [Plan and Limit Model](#plan-and-limit-model)
9. [Reporting and Export](#reporting-and-export)
10. [Validation and Tests](#validation-and-tests)
11. [Deployment Notes](#deployment-notes)
12. [Security Notes](#security-notes)
13. [Roadmap Suggestions](#roadmap-suggestions)

## Project Overview

The application is designed to solve four core problems:

- Keep financial activity in a single source of truth.
- Extract structured data from receipts/invoices via OCR.
- Let users review and correct OCR output before saving records.
- Enforce plan-based monthly limits for receipts and transactions.

## Key Features

- User registration, login, and logout flows.
- Dashboard with monthly summary:
  - Total income
  - Total expense
  - Net balance
  - Category-based expense distribution
- Receipt/invoice upload with Cloudinary storage.
- OCR.space integration for automatic extraction:
  - Vendor
  - Amount
  - Date
  - Raw OCR text
- Review screen for manual correction before transaction creation.
- Full transaction management (create, list, edit, delete).
- Category management (system categories + user custom categories).
- CSV and PDF export for transactions.
- Stripe subscription workflows:
  - Plan selection
  - Checkout session
  - Billing portal session
  - Webhook-based subscription sync
- Monthly plan limit enforcement:
  - Receipt upload limits
  - Transaction creation limits

## Technology Stack

- Backend: Django 6
- Database: PostgreSQL via dj-database-url
- Frontend: Django Templates + Bootstrap 5
- Static files: WhiteNoise
- Media storage: Cloudinary
- OCR provider: OCR.space
- Payments and subscriptions: Stripe
- PDF generation: ReportLab
- WSGI server: Gunicorn

## Architecture and Modules

- accounts
  - Signup and authentication screens
- core
  - Home and dashboard
  - Category management
  - Subscription and Stripe integration
  - Plan/usage limit logic
- receipts
  - Receipt upload and OCR processing
  - Receipt detail, review, and delete flows
- transactions
  - Transaction CRUD
  - Date/month filtering
  - CSV and PDF export

## Installation and Local Setup

### 1) Prerequisites

- Python 3.11+
- pip
- PostgreSQL access (local or cloud)

### 2) Clone repository

```bash
git clone <repository-url>
cd Smart_Accounts_Management
```

### 3) Create virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4) Configure environment variables

Set variables in your shell or use `env.py` for local development.

### 5) Run database migrations

```bash
python manage.py migrate
```

### 6) Seed default categories

```bash
python manage.py seed_categories
```

### 7) Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 8) Start development server

```bash
python manage.py runserver
```

## Environment Variables

The following variables should be configured:

- `SECRET_KEY`
- `DATABASE_URL`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`
- `OCR_SPACE_API_KEY`
- `STRIPE_PUBLIC_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_PRICE_BASIC`
- `STRIPE_PRICE_PREMIUM`
- `STRIPE_WEBHOOK_SECRET`
- `SITE_URL`

## User Flow

1. User signs up or logs in.
2. User views monthly metrics on the dashboard.
3. User uploads a receipt or invoice.
4. OCR service extracts candidate fields.
5. User reviews and corrects extracted values.
6. Confirmed data is saved as a transaction.
7. Transactions can be filtered and exported.

## Plan and Limit Model

Default plan rules:

- Basic
  - Max receipts per month: 25
  - Max transactions per month: 100
- Premium
  - Unlimited receipts
  - Unlimited transactions

Limit checks are enforced for both receipt uploads and transaction creation.

## Reporting and Export

- CSV export: filtered scope or all records
- PDF export: filtered scope or all records
- PDF layout uses row-based tabular output

## Validation and Tests

```bash
python manage.py check
python manage.py test
```

## Deployment Notes

- Production should run with `DEBUG=False`.
- Collect static files before deployment:

```bash
python manage.py collectstatic --noinput
```

- Example Gunicorn command:

```bash
gunicorn smart_account_management.wsgi
```

## Security Notes

- Never commit secrets, API keys, or database credentials.
- Manage production secrets using environment-level configuration.
- Verify Stripe webhook signatures with the correct webhook secret.

## Roadmap Suggestions

- Add OCR confidence scores and field-level validation insights.
- Move OCR processing to asynchronous workers (Celery or RQ).
- Increase unit and integration test coverage.
- Add role-based authorization and audit logging.
