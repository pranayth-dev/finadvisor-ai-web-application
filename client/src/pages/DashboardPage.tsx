import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  TrendingUp, TrendingDown, Wallet, Percent, Heart,
  Plus, ArrowRight, RefreshCw, Bell
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, LineChart, Line, ResponsiveContainer
} from 'recharts'
import api from '../services/api'
import type { DashboardData, TrendData } from '../types'
import { formatCurrency, formatDate, formatDateShort, currentMonth, currentYear, MONTH_NAMES } from '../utils/formatters'
import toast from 'react-hot-toast'

const PIE_COLORS = ['#427A76', '#254B45', '#6BBF9B', '#A8D5C2', '#F4A261', '#E76F51', '#2A9D8F', '#264653']

function StatCard({ title, value, subtitle, icon: Icon, color, trend }: {
  title: string; value: string; subtitle?: string; icon: any; color: string; trend?: 'up' | 'down' | 'neutral'
}) {
  return (
    <div className="card flex items-start gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
        <Icon size={20} className="text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{title}</p>
        <p className="text-xl font-bold text-gray-800 mt-0.5 truncate">{value}</p>
        {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardData | null>(null)
  const [trends, setTrends] = useState<TrendData[]>([])
  const [loading, setLoading] = useState(true)
  const [month, setMonth] = useState(currentMonth())
  const [year, setYear] = useState(currentYear())

  async function load() {
    setLoading(true)
    try {
      const [dashRes, trendRes] = await Promise.all([
        api.get('/dashboard', { params: { month, year } }),
        api.get('/dashboard/trends', { params: { months: 6 } }),
      ])
      setData(dashRes.data)
      setTrends(trendRes.data.trends)
    } catch {
      toast.error('Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [month, year])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const summary = data?.summary
  const health = data?.health_score

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800 dark:text-white">Financial Overview</h1>
          <p className="text-sm text-gray-500">Track your income, expenses and savings</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={month}
            onChange={e => setMonth(Number(e.target.value))}
            className="input py-1.5 text-sm w-auto"
          >
            {MONTH_NAMES.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
          </select>
          <select
            value={year}
            onChange={e => setYear(Number(e.target.value))}
            className="input py-1.5 text-sm w-auto"
          >
            {[currentYear(), currentYear() - 1, currentYear() - 2].map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          <button onClick={load} className="btn-secondary py-1.5 px-3">
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        <StatCard
          title="Total Income"
          value={formatCurrency(summary?.total_income ?? 0)}
          subtitle={`${MONTH_NAMES[(month ?? 1) - 1]} ${year}`}
          icon={TrendingUp}
          color="bg-green-500"
        />
        <StatCard
          title="Total Expenses"
          value={formatCurrency(summary?.total_expenses ?? 0)}
          subtitle="All categories"
          icon={TrendingDown}
          color="bg-red-400"
        />
        <StatCard
          title="Net Savings"
          value={formatCurrency(summary?.net_savings ?? 0)}
          subtitle="Income − Expenses"
          icon={Wallet}
          color={(summary?.net_savings ?? 0) >= 0 ? "bg-teal-500" : "bg-orange-500"}
        />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        <StatCard
          title="Savings Rate"
          value={`${summary?.savings_rate?.toFixed(1) ?? 0}%`}
          subtitle="Of total income"
          icon={Percent}
          color="bg-blue-500"
        />
        <StatCard
          title="Monthly Bills"
          value={formatCurrency(summary?.monthly_bills_total ?? 0)}
          subtitle="Recurring payments"
          icon={Bell}
          color="bg-purple-500"
        />
        <StatCard
          title="Health Score"
          value={`${health?.score ?? 0}/100`}
          subtitle={health?.grade}
          icon={Heart}
          color={
            (health?.score ?? 0) >= 80 ? 'bg-green-500'
            : (health?.score ?? 0) >= 60 ? 'bg-teal-500'
            : (health?.score ?? 0) >= 40 ? 'bg-yellow-500'
            : 'bg-red-500'
          }
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Income vs Expenses Bar */}
        <div className="card lg:col-span-2">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Income vs Expenses (6 Months)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={trends} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v: number) => `₹${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: unknown) => formatCurrency(Number(v))} />
              <Legend />
              <Bar dataKey="income" name="Income" fill="#427A76" radius={[3, 3, 0, 0]} />
              <Bar dataKey="expenses" name="Expenses" fill="#E76F51" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Expense by Category Pie */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Expenses by Category</h3>
          {data?.category_spending && data.category_spending.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie
                    data={data.category_spending}
                    dataKey="amount"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={70}
                  >
                    {data.category_spending.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: unknown) => formatCurrency(Number(v))} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1 mt-2">
                {data.category_spending.slice(0, 4).map((c, i) => (
                  <div key={c.category} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                      <span className="text-gray-600">{c.category}</span>
                    </div>
                    <span className="font-medium text-gray-700">{formatCurrency(c.amount)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
              No expense data
            </div>
          )}
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Savings Trend */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Savings Trend</h3>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={trends} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v: number) => `₹${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: unknown) => formatCurrency(Number(v))} />
              <Line type="monotone" dataKey="savings" name="Savings" stroke="#427A76" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Budget Utilization */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Budget Utilization</h3>
          {data?.budgets && data.budgets.length > 0 ? (
            <div className="space-y-3">
              {data.budgets.slice(0, 5).map(b => (
                <div key={b.id}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-600 font-medium">{b.category}</span>
                    <span className={
                      b.status === 'over_budget' ? 'text-red-600 font-semibold'
                      : b.status === 'near_limit' ? 'text-orange-600 font-semibold'
                      : 'text-gray-500'
                    }>
                      {b.utilization_percent}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        b.status === 'over_budget' ? 'bg-red-500'
                        : b.status === 'near_limit' ? 'bg-orange-400'
                        : 'bg-teal-500'
                      }`}
                      style={{ width: `${Math.min(100, b.utilization_percent)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs mt-0.5 text-gray-400">
                    <span>Spent: {formatCurrency(b.spent)}</span>
                    <span>Limit: {formatCurrency(b.limit_amount)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-36 gap-3">
              <p className="text-sm text-gray-400">No budgets set for this month</p>
              <button onClick={() => navigate('/budgets')} className="btn-primary text-xs py-1.5 px-3">
                Create Budget
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Upcoming Bills */}
      {data?.upcoming_bills && data.upcoming_bills.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-1">
              <Bell size={15} className="text-teal-500" /> Upcoming Bills (next 30 days)
            </h3>
            <button onClick={() => navigate('/bills')}
              className="text-xs text-teal-600 hover:underline flex items-center gap-1">
              Manage Bills <ArrowRight size={12} />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.upcoming_bills.map(b => (
              <div key={b.id} className={`flex items-center justify-between p-3 rounded-xl border ${
                b.is_overdue ? 'bg-red-50 border-red-200' : (b.days_until_due ?? 99) <= 3 ? 'bg-orange-50 border-orange-200' : 'bg-gray-50 border-gray-100'
              }`}>
                <div>
                  <p className="text-sm font-medium text-gray-700">{b.name}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {b.is_overdue ? (
                      <span className="text-red-600 font-medium">Overdue</span>
                    ) : (b.days_until_due ?? 0) === 0 ? (
                      <span className="text-orange-600 font-medium">Due today</span>
                    ) : (
                      `Due in ${b.days_until_due} day${(b.days_until_due ?? 0) !== 1 ? 's' : ''}`
                    )}
                  </p>
                </div>
                <span className="text-sm font-bold text-gray-800">{formatCurrency(b.amount)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recent Transactions */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700">Recent Transactions</h3>
            <button onClick={() => navigate('/transactions')}
              className="text-xs text-teal-600 hover:underline flex items-center gap-1">
              View all <ArrowRight size={12} />
            </button>
          </div>
          {data?.recent_transactions && data.recent_transactions.length > 0 ? (
            <div className="space-y-2">
              {data.recent_transactions.slice(0, 7).map(t => (
                <div key={t.id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                      t.type === 'income' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                    }`}>
                      {t.category[0]}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700 truncate max-w-[180px]">{t.description}</p>
                      <p className="text-xs text-gray-400">{t.category} · {formatDateShort(t.date)}</p>
                    </div>
                  </div>
                  <span className={`text-sm font-semibold ${
                    t.type === 'income' ? 'text-green-600' : 'text-red-500'
                  }`}>
                    {t.type === 'income' ? '+' : '-'}{formatCurrency(t.amount)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-32 gap-3">
              <p className="text-sm text-gray-400">No transactions yet</p>
              <button onClick={() => navigate('/transactions')} className="btn-primary text-xs py-1.5 px-3">
                Add Transaction
              </button>
            </div>
          )}
        </div>

        {/* Savings Goals */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700">Savings Goals</h3>
            <button onClick={() => navigate('/goals')}
              className="text-xs text-teal-600 hover:underline flex items-center gap-1">
              All <ArrowRight size={12} />
            </button>
          </div>
          {data?.goals && data.goals.length > 0 ? (
            <div className="space-y-4">
              {data.goals.slice(0, 3).map(g => (
                <div key={g.id}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-medium text-gray-700 truncate max-w-[140px]">{g.name}</span>
                    <span className="text-teal-600 font-semibold">{g.progress_percent}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-teal-500 transition-all"
                      style={{ width: `${g.progress_percent}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs mt-0.5 text-gray-400">
                    <span>{formatCurrency(g.current_amount)}</span>
                    <span>{formatCurrency(g.target_amount)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-32 gap-3">
              <p className="text-sm text-gray-400">No savings goals</p>
              <button onClick={() => navigate('/goals')} className="btn-primary text-xs py-1.5 px-3">
                Create Goal
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Quick Actions</h3>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => navigate('/transactions')} className="btn-primary text-sm py-2 px-4 flex items-center gap-2">
            <Plus size={15} /> Add Income
          </button>
          <button onClick={() => navigate('/transactions')} className="btn-secondary text-sm py-2 px-4 flex items-center gap-2">
            <Plus size={15} /> Add Expense
          </button>
          <button onClick={() => navigate('/budgets')} className="btn-secondary text-sm py-2 px-4 flex items-center gap-2">
            <Plus size={15} /> New Budget
          </button>
          <button onClick={() => navigate('/goals')} className="btn-secondary text-sm py-2 px-4 flex items-center gap-2">
            <Plus size={15} /> New Goal
          </button>
          <button onClick={() => navigate('/advisor')} className="btn-secondary text-sm py-2 px-4 flex items-center gap-2">
            <ArrowRight size={15} /> AI Insights
          </button>
        </div>
      </div>
    </div>
  )
}
