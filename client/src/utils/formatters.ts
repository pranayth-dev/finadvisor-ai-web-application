/**
 * Format a number as Indian Rupees
 */
export function formatCurrency(amount: number, decimals = 0): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(amount)
}

/**
 * Format a number with Indian number system commas (no currency symbol)
 */
export function formatNumber(amount: number): string {
  return new Intl.NumberFormat('en-IN').format(amount)
}

/**
 * Format ISO date string to human readable
 */
export function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function formatDateShort(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

/**
 * Return today's date as YYYY-MM-DD
 */
export function todayISO(): string {
  return new Date().toISOString().split('T')[0]
}

/**
 * Return first day of current month as YYYY-MM-DD
 */
export function firstOfMonthISO(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}

export function currentMonth(): number { return new Date().getMonth() + 1 }
export function currentYear(): number { return new Date().getFullYear() }

export const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

export const EXPENSE_CATEGORIES = [
  'Food', 'Transport', 'Shopping', 'Housing', 'Education',
  'Healthcare', 'Utilities', 'Entertainment', 'Investments', 'Other',
]

export const INCOME_CATEGORIES = [
  'Salary', 'Freelancing', 'Business', 'Investments', 'Other Income',
]

export const ALL_CATEGORIES = [...INCOME_CATEGORIES, ...EXPENSE_CATEGORIES]

export const PAYMENT_METHODS = [
  'Cash', 'UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Cheque', 'Other',
]

export const GOAL_CATEGORIES = [
  'Emergency Fund', 'Electronics', 'Travel', 'Education', 'Vehicle', 'Housing', 'Healthcare', 'Other',
]

export function getPriorityColor(priority: string): string {
  switch (priority) {
    case 'critical': return 'text-red-600 bg-red-50 border-red-200'
    case 'high': return 'text-orange-600 bg-orange-50 border-orange-200'
    case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    default: return 'text-green-600 bg-green-50 border-green-200'
  }
}

export function getInsightIcon(type: string): string {
  switch (type) {
    case 'spending': return '💸'
    case 'savings': return '💰'
    case 'budget': return '📊'
    case 'goal': return '🎯'
    case 'health': return '❤️'
    default: return '💡'
  }
}
