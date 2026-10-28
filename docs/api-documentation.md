# API Documentation — FinAdvisor AI

Base URL: `http://localhost:5000/api`

All protected endpoints require: `Authorization: Bearer <access_token>`

---

## Authentication

### POST /auth/register
Register a new user.

**Request body:**
```json
{ "email": "user@example.com", "password": "Secure@123", "first_name": "Priya", "last_name": "Sharma" }
```
**Response 201:**
```json
{ "access_token": "...", "refresh_token": "...", "user": { ... } }
```

### POST /auth/login
**Request:** `{ "email": "...", "password": "..." }`
**Response 200:** `{ "access_token": "...", "user": { ... } }`

### GET /auth/me *(protected)*
Returns the current user object.

### POST /auth/logout *(protected)*
Clears server-side session.

### POST /auth/change-password *(protected)*
**Request:** `{ "current_password": "...", "new_password": "..." }`

---

## Transactions

### GET /transactions *(protected)*
**Query params:** `page`, `per_page`, `type`, `category`, `search`, `start_date`, `end_date`, `sort_by`, `sort_order`

**Response:**
```json
{ "transactions": [...], "total": 42, "page": 1, "per_page": 15, "pages": 3 }
```

### POST /transactions *(protected)*
```json
{ "description": "Salary", "amount": 75000, "type": "income", "category": "Salary", "date": "2024-06-01" }
```

### PUT /transactions/:id *(protected)*
Full update (same fields as POST).

### DELETE /transactions/:id *(protected)*

---

## Dashboard

### GET /dashboard *(protected)*
**Query params:** `month` (1–12), `year`

**Response:**
```json
{
  "summary": { "total_income": 75000, "total_expenses": 42000, "net_savings": 33000, "savings_rate": 44.0 },
  "category_spending": [...],
  "budgets": [...],
  "goals": [...],
  "recent_transactions": [...],
  "health_score": { "score": 72, "grade": "Good", ... }
}
```

### GET /dashboard/trends *(protected)*
**Query params:** `months` (default 6)

---

## Budgets

### GET /budgets *(protected)*
**Query params:** `month`, `year`
Returns budgets with calculated `spent`, `remaining`, `utilization_percent`, `status`.

### POST /budgets *(protected)*
```json
{ "category": "Food", "limit_amount": 8000, "month": 6, "year": 2024 }
```

### PUT /budgets/:id *(protected)*
Update `limit_amount` or `notes`.

### DELETE /budgets/:id *(protected)*

---

## Savings Goals

### GET /goals *(protected)*
**Query params:** `include_completed` (bool)
Returns goals with `progress_percent`, `remaining_amount`, `monthly_needed`.

### POST /goals *(protected)*
```json
{ "name": "Emergency Fund", "target_amount": 225000, "current_amount": 45000, "target_date": "2025-06-01" }
```

### PUT /goals/:id *(protected)*
### DELETE /goals/:id *(protected)*

---

## AI Advisor

### GET /advisor/insights *(protected)*
Returns stored insights ordered by created_at desc.

### POST /advisor/analyze *(protected)*
Runs the financial rules engine on current user data, stores new insights.
**Response:**
```json
{ "insights": [...], "count": 8, "generated_at": "...", "note": "Informational only..." }
```

### GET /advisor/health-score *(protected)*
```json
{ "score": 72, "grade": "Good", "breakdown": [...], "strengths": [...], "areas_for_improvement": [...] }
```

---

## Reports

### GET /reports/monthly *(protected)*
**Query params:** `month`, `year`
Returns full monthly summary including `financial_story` text.

### GET /reports/categories *(protected)*
**Query params:** `start_date`, `end_date`
Category-wise spending aggregation.

### GET /reports/export *(protected)*
Returns CSV file of transactions.

---

## Profile & Settings

### GET /profile *(protected)*
### PUT /profile *(protected)*
Update: `first_name`, `last_name`, `phone`, `currency`, `monthly_income_preference`, `theme`, `account_mode`, notification flags.

### DELETE /profile/delete *(protected)*
**Request:** `{ "password": "..." }` (confirmation required)

---

## Notifications

### GET /notifications *(protected)*
Returns `{ notifications: [...], unread_count: N }`

### PUT /notifications/:id/read *(protected)*
### PUT /notifications/read-all *(protected)*

---

## Family

### GET /family *(protected)*
### POST /family/create *(protected)*
**Request:** `{ "name": "Sharma Family" }`

### GET /family/overview *(protected)*
**Query params:** `month`, `year`
Returns combined income/expenses and per-member breakdown.

---

## Error Responses

All errors return:
```json
{ "error": "Human-readable message" }
```
or for validation:
```json
{ "errors": ["field error 1", "field error 2"] }
```

HTTP status codes: 200, 201, 400, 401, 403, 404, 409, 500
