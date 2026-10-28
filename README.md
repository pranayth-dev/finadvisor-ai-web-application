# FinAdvisor AI — Smart Money. Better Decisions.

A full-stack personal finance management application with:
- React + TypeScript + Vite frontend
- Python Flask + SQLAlchemy backend (SQLite by default)
- Optional MongoDB integration
- Real AI chat via Google Gemini or OpenAI

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone and set up environment

```powershell
# In PowerShell — from the project root
Copy-Item .env.example .env
# Edit .env — set SECRET_KEY, JWT_SECRET_KEY, and optionally GEMINI_API_KEY
notepad .env
```

### 2. Start the backend

```powershell
cd server
.\venv\Scripts\python run.py
```

The Flask server starts on **http://localhost:5000**.

If `venv` does not exist yet:
```powershell
cd server
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\python run.py
```

### 3. Start the frontend (separate terminal)

```powershell
cd client
# First time only:
npm install

# Start dev server:
npm run dev
```

The Vite dev server starts on **http://localhost:5173**.

---

## Required Environment Variables

Copy `.env.example` to `.env` and set the following in the `server/` directory (or project root):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | `dev-secret-key-…` | Flask session secret |
| `JWT_SECRET_KEY` | Yes | `dev-jwt-secret-…` | JWT signing key |
| `DATABASE_URL` | No | `sqlite:///finadvisor.db` | SQLite database path |
| `FRONTEND_URL` | No | `http://localhost:5173` | Allowed CORS origin |
| `GEMINI_API_KEY` | No | — | Google Gemini 1.5 Flash key (free tier) |
| `OPENAI_API_KEY` | No | — | OpenAI GPT-4o-mini key |
| `MONGODB_URI` | No | — | MongoDB connection URI |
| `MONGODB_DB_NAME` | No | `finadvisor` | MongoDB database name |

> **AI Advisor:** Without a Gemini or OpenAI key the advisor uses a deterministic built-in fallback engine. For real LLM responses, set `GEMINI_API_KEY` (free at https://aistudio.google.com/app/apikey).

---

## MongoDB Setup (Optional)

The application runs on SQLite by default. MongoDB is an optional additional store.

### Option A — Local MongoDB

1. Download and install MongoDB Community Server from https://www.mongodb.com/try/download/community
2. Start MongoDB:
   ```powershell
   mongod --dbpath C:\data\db
   ```
3. Add to `.env`:
   ```
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DB_NAME=finadvisor
   ```

### Option B — MongoDB Atlas (cloud, free tier)

1. Create an account at https://www.mongodb.com/cloud/atlas
2. Create a free cluster
3. Get your connection string and add to `.env`:
   ```
   MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/
   MONGODB_DB_NAME=finadvisor
   ```

### Migrate existing SQLite data to MongoDB

```powershell
cd server

# 1. Dry run — inspect without writing
.\venv\Scripts\python migrate_to_mongo.py --dry-run

# 2. Full migration
.\venv\Scripts\python migrate_to_mongo.py

# 3. Validate record counts
.\venv\Scripts\python migrate_to_mongo.py --validate-only
```

> The migration script **never deletes** the original SQLite database. Re-running is safe — it skips already-migrated records. Back up `instance/finadvisor.db` before running if your data is important.

---

## Running Tests

```powershell
cd server
.\venv\Scripts\python -m pytest tests/ -v
```

**32 tests** covering:
- Authentication (register, login, JWT, me, change-password)
- Transactions (CRUD, access control)
- Dashboard calculations
- Budgets (create, spending calculation)
- Savings goals (create, progress)
- Health score (range, with data)
- Advisor (analyze, no-duplicate insights)
- Insight delete (ownership, deduplication)
- Family finance (create group, invite/accept, permission enforcement)
- Invalid request handling

---

## Architecture

### Frontend (`client/src/`)

| File | Purpose |
|------|---------|
| `App.tsx` | Routes: `/landing` (public), `/login`, `/register`, authenticated pages |
| `pages/LandingPage.tsx` | Public landing page — sections: hero, features, how-it-works, benefits, security |
| `pages/AdvisorPage.tsx` | AI Advisor with 4 tabs: Finance Chat, My Finances, Insights (Show/Delete), Health Score |
| `pages/FamilyPage.tsx` | Family Finance: overview, goals, members (invite/remove), transactions |
| `hooks/useAuth.tsx` | JWT auth context |
| `services/api.ts` | Axios client with JWT interceptor |

### Backend (`server/app/`)

| File | Purpose |
|------|---------|
| `__init__.py` | Flask factory — registers blueprints, initializes SQLAlchemy + MongoDB |
| `models.py` | SQLAlchemy models: User, Transaction, Budget, SavingsGoal, Bill, FinancialInsight, Notification, ChatMessage, FamilyGroup, FamilyInvitation, FamilySavingsGoal |
| `mongo.py` | MongoDB connection manager with index definitions |
| `routes/advisor.py` | `/api/advisor` — chat, analyze, insights CRUD (including DELETE), health score |
| `routes/family.py` | `/api/family` — group, invite, respond, members, transactions, goals |
| `services/advisor.py` | LLM integration (Gemini/OpenAI/built-in), financial context builder, insights engine |
| `config.py` | Config classes (development/production) |
| `migrate_to_mongo.py` | SQLite → MongoDB migration utility |

---

## Implemented Features

### ✅ Feature 1: Professional Landing Page
- Responsive public page with navbar, hero, features (10 cards), how it works, benefits, security, and footer
- Unauthenticated visitors see the landing page at `/landing`
- Login/Register buttons route to existing auth pages
- Authenticated users bypass the landing page and go directly to `/dashboard`

### ✅ Feature 2: Personal Finance AI Advisor
- Uses Gemini 1.5 Flash (free tier) → OpenAI GPT-4o-mini → built-in deterministic fallback
- Injects user's real transactions, budgets, goals, bills into system prompt
- Supports all 10 predefined personal questions + custom questions
- Maintains multi-turn conversation history (saved per user in `chat_messages` table)
- Personal and General advisor modes kept strictly separate

### ✅ Feature 3: General Finance AI Assistant
- Answers general finance questions without accessing personal data
- Enhanced system prompt includes full FinAdvisor AI app navigation documentation
- Answers questions like "How do I add a transaction?" with exact steps, fields, and validation rules
- Supports follow-up questions and maintains conversation context

### ✅ Feature 4: Insights Tab
- **Deduplication**: Running "Run Analysis" multiple times does not create duplicate insights for the same month
- **Show button**: Opens a detail modal with full explanation, period, category, type, and generated-at date
- **Delete button**: Asks for confirmation, deletes only the selected insight for the authenticated user, updates UI immediately
- Deleting an insight never deletes transactions, budgets, or goals

### ✅ Feature 5: Family Finance Module
- Create a family group (owner role)
- Owner can invite members by email (must be registered users)
- Invited users see invitation banners and can Accept or Decline
- Owner can remove members
- Member overview tab: combined income/expenses/savings, category breakdown, recent transactions
- Shared savings goals with progress tracking and contribution recording
- Transactions tab showing all members' transactions for the selected period
- Owner-only permissions on invite/remove/edit-goal/delete-goal

### ✅ Feature 6: MongoDB Integration
- `server/app/mongo.py`: connection manager, graceful fallback if MongoDB unavailable
- `server/migrate_to_mongo.py`: safe SQLite-to-MongoDB migration with dry-run, deduplication, and validation modes
- All required indexes created automatically
- BSON ObjectId handling, connection validation on startup
- `MONGODB_URI` and `MONGODB_DB_NAME` configurable via environment variables

### ✅ Feature 7: Security
- All financial records are scoped to authenticated users via JWT
- Insight delete verifies ownership — users cannot delete other users' records
- Family operations enforce owner/member roles on the backend
- Input validation on all API endpoints
- API keys kept exclusively in environment variables (never in frontend)
- Errors return safe messages without stack traces

---

## Known Limitations

1. The existing SQLite schema has a circular foreign key between `users` and `family_groups` (a SQLite limitation). The test suite works correctly; the SAWarning is cosmetic.
2. JWT key-length warnings in tests are from the test-config short key — production keys should be 32+ bytes.
3. MongoDB is optional. If `MONGODB_URI` is not set, the app runs on SQLite only. Migrating data from SQLite to MongoDB requires running `migrate_to_mongo.py` manually.
4. The AI advisor requires at least one AI API key for real LLM responses; without one, the built-in deterministic engine handles the 10 predefined questions but may give generic answers for unusual questions.
