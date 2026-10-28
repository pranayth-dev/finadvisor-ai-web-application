export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  phone?: string
  account_mode: 'individual' | 'family'
  currency: string
  monthly_income_preference: number
  theme: 'light' | 'dark'
  notification_budget_alerts: boolean
  notification_goal_milestones: boolean
  notification_monthly_summary: boolean
  family_group_id?: number
  created_at: string
}

export interface Transaction {
  id: number
  user_id: number
  description: string
  amount: number
  type: 'income' | 'expense'
  category: string
  date: string
  notes?: string
  payment_method?: string
  is_shared: boolean
  family_group_id?: number
  created_at: string
}

export interface Budget {
  id: number
  user_id: number
  category: string
  limit_amount: number
  period: string
  month: number
  year: number
  notes?: string
  spent: number
  remaining: number
  utilization_percent: number
  status: 'within_budget' | 'near_limit' | 'over_budget'
  created_at: string
}

export interface SavingsGoal {
  id: number
  user_id: number
  name: string
  target_amount: number
  current_amount: number
  remaining_amount: number
  progress_percent: number
  target_date?: string
  category: string
  notes?: string
  is_completed: boolean
  monthly_needed?: number
  created_at: string
}

export interface FinancialInsight {
  id: number
  user_id: number
  title: string
  message: string
  insight_type: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  category?: string
  action_label?: string
  action_url?: string
  is_read: boolean
  month?: number
  year?: number
  created_at: string
}

export interface Notification {
  id: number
  user_id: number
  title: string
  message: string
  notification_type: string
  is_read: boolean
  link?: string
  created_at: string
}

export interface DashboardSummary {
  total_income: number
  total_expenses: number
  net_savings: number
  savings_rate: number
  month: number
  year: number
  monthly_bills_total: number
}

export interface Bill {
  id: number
  user_id: number
  name: string
  amount: number
  category: string
  frequency: 'monthly' | 'weekly' | 'yearly' | 'one-time'
  due_day?: number
  next_due_date?: string
  is_active: boolean
  auto_pay: boolean
  notes?: string
  payment_method?: string
  days_until_due?: number
  is_overdue: boolean
  created_at: string
}

export interface HealthScore {
  score: number
  grade: string
  breakdown: { factor: string; score: number; max: number; note: string }[]
  strengths: string[]
  areas_for_improvement: string[]
}

export interface DashboardData {
  summary: DashboardSummary
  category_spending: { category: string; amount: number }[]
  budgets: Budget[]
  goals: SavingsGoal[]
  recent_transactions: Transaction[]
  upcoming_bills: Bill[]
  health_score: HealthScore
}

export interface TrendData {
  month: string
  month_num: number
  year: number
  income: number
  expenses: number
  savings: number
}

export interface MonthlyReport {
  month: number
  year: number
  month_name: string
  total_income: number
  total_expenses: number
  net_savings: number
  savings_rate: number
  income_by_category: { category: string; amount: number }[]
  expense_by_category: { category: string; amount: number }[]
  transaction_count: number
  financial_story: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  user: User
  message: string
}

export interface SavedChatMessage {
  id: number
  user_id?: number
  advisor_type: 'personal' | 'general'
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  ai_provider?: string
  created_at: string
}

export type TransactionFormData = Omit<Transaction, 'id' | 'user_id' | 'created_at' | 'is_shared' | 'family_group_id'>
export type BudgetFormData = Pick<Budget, 'category' | 'limit_amount' | 'month' | 'year' | 'notes'>
export type GoalFormData = Pick<SavingsGoal, 'name' | 'target_amount' | 'current_amount' | 'target_date' | 'category' | 'notes'>
