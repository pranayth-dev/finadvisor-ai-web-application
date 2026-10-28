# Architecture — FinAdvisor AI

## Overview

FinAdvisor AI uses a standard two-tier architecture:
- React SPA frontend served by Vite dev server (or Nginx in production)
- Flask REST API backend with SQLite database

```
Browser (React SPA)
        │  HTTP/JSON (JWT Bearer token)
        ▼
Flask REST API  (localhost:5000)
        │
        ▼
SQLAlchemy ORM
        │
        ▼
SQLite database  (server/finadvisor.db)
```

## Request Flow

1. User visits http://localhost:5173
2. React app loads; checks `localStorage` for JWT token
3. If valid, fetches user profile from `/api/auth/me`
4. React Router serves protected pages
5. Each page fetches data via Axios calls to `/api/*` (proxied to port 5000 by Vite)
6. Flask validates JWT, queries SQLite, returns JSON
7. React renders the data

## Security

- Passwords hashed with bcrypt (12 salt rounds)
- JWT tokens (24-hour expiry) stored in `localStorage`
- All protected endpoints require `Authorization: Bearer <token>`
- User-scoped queries: every SQL query includes `user_id = current_user.id`
- Input validation on both frontend and backend
- CORS restricted to configured `FRONTEND_URL`

## AI Engine

The Financial Advisor uses a transparent Python rules engine in `server/app/services/advisor.py`. No external API is required.

Rules applied:
1. Savings rate classification (poor < 10% / average < 20% / good < 30% / excellent ≥ 30%)
2. Budget breach detection (>100% = over budget, ≥80% = near limit)
3. Month-over-month category spending delta (>50% increase flagged)
4. Goal deadline calculation (monthly_needed = remaining / months_left)
5. Emergency fund detection and recommendation
6. Missing budget detection

The `OPENAI_API_KEY` environment variable is a prepared extension point for enriching rule output with LLM-generated text, but the system works fully without it.

## Financial Health Score Algorithm

Score: 0–100 composed of 4 factors:

| Factor | Max Points | Criteria |
|--------|-----------|----------|
| Savings Rate | 30 | ≥30% = 30pts, ≥20% = 22pts, ≥10% = 14pts |
| Expense-to-Income Ratio | 25 | ≤50% = 25pts, ≤70% = 18pts, ≤90% = 10pts |
| Budget Adherence | 25 | % of budgets within limit |
| Emergency Fund | 20 | Progress toward emergency savings goal |

Grade: Excellent (≥80), Good (≥60), Fair (≥40), Needs Improvement (<40)
