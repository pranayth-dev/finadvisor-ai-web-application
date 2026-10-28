# Database Design — FinAdvisor AI

## Tables

### users
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| email | VARCHAR(255) UNIQUE | Indexed |
| password_hash | VARCHAR(255) | bcrypt |
| first_name | VARCHAR(100) | |
| last_name | VARCHAR(100) | |
| phone | VARCHAR(20) | Nullable |
| account_mode | VARCHAR(20) | 'individual' or 'family' |
| currency | VARCHAR(10) | Default 'INR' |
| monthly_income_preference | FLOAT | Planning reference |
| theme | VARCHAR(20) | 'light' or 'dark' |
| notification_budget_alerts | BOOLEAN | |
| notification_goal_milestones | BOOLEAN | |
| notification_monthly_summary | BOOLEAN | |
| family_group_id | FK → family_groups | Nullable |
| is_active | BOOLEAN | Soft delete flag |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### transactions
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | FK → users | Indexed |
| description | VARCHAR(255) | |
| amount | FLOAT | Must be > 0 |
| type | VARCHAR(20) | 'income' or 'expense' |
| category | VARCHAR(100) | |
| date | DATE | Indexed |
| notes | TEXT | Nullable |
| payment_method | VARCHAR(50) | |
| is_shared | BOOLEAN | Family shared expense |
| family_group_id | FK → family_groups | Nullable |
| created_at / updated_at | DATETIME | |

### budgets
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | FK → users | Indexed |
| category | VARCHAR(100) | |
| limit_amount | FLOAT | |
| period | VARCHAR(20) | 'monthly' |
| month | INTEGER | 1–12 |
| year | INTEGER | |
| notes | TEXT | Nullable |
| created_at / updated_at | DATETIME | |
| UNIQUE | (user_id, category, month, year) | |

### savings_goals
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | FK → users | Indexed |
| name | VARCHAR(255) | |
| target_amount | FLOAT | |
| current_amount | FLOAT | Default 0 |
| target_date | DATE | Nullable |
| category | VARCHAR(100) | |
| notes | TEXT | Nullable |
| is_completed | BOOLEAN | Auto-set when current ≥ target |
| created_at / updated_at | DATETIME | |

### financial_insights
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | FK → users | Indexed |
| title | VARCHAR(255) | |
| message | TEXT | |
| insight_type | VARCHAR(50) | spending/savings/budget/goal/info |
| priority | VARCHAR(20) | critical/high/medium/low |
| category | VARCHAR(100) | Nullable |
| action_label / action_url | VARCHAR | Nullable |
| is_read | BOOLEAN | |
| month / year | INTEGER | Nullable |
| created_at | DATETIME | |

### notifications
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | FK → users | Indexed |
| title | VARCHAR(255) | |
| message | TEXT | |
| notification_type | VARCHAR(50) | budget/goal/summary/info |
| is_read | BOOLEAN | |
| link | VARCHAR(255) | Nullable |
| created_at | DATETIME | |

### family_groups
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | VARCHAR(255) | |
| created_by | FK → users | |
| description | TEXT | Nullable |
| created_at | DATETIME | |

## Relationships

- `users.family_group_id` → `family_groups.id` (many users in one group)
- `transactions.user_id` → `users.id` (cascade delete)
- `budgets.user_id` → `users.id` (cascade delete)
- `savings_goals.user_id` → `users.id` (cascade delete)
- `financial_insights.user_id` → `users.id` (cascade delete)
- `notifications.user_id` → `users.id` (cascade delete)

## Notes

- Database created automatically by SQLAlchemy `db.create_all()` on first run.
- All queries filter by `user_id` to enforce data isolation.
- Soft delete on users (`is_active = False`) preserves data for recovery.
- Indexes on `user_id` and `date` columns for performance.
