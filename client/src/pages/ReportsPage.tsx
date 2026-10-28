import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line
} from 'recharts'
import api from '../services/api'
import type { MonthlyReport } from '../types'
import { formatCurrency, MONTH_NAMES, currentMonth, currentYear } from '../utils/formatters'
import toast from 'react-hot-toast'
import { FileText, BookOpen, Download } from 'lucide-react'

async function downloadCSV() {
  try {
    const res = await api.get('/reports/export', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'transactions.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch {
    toast.error('Failed to export CSV')
  }
}

const PIE_COLORS = ['#427A76', '#254B45', '#6BBF9B', '#A8D5C2', '#F4A261', '#E76F51', '#2A9D8F', '#264653', '#8ECAE6', '#023047']

export default function ReportsPage() {
  const [report, setReport] = useState<MonthlyReport | null>(null)
  const [trends, setTrends] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [month, setMonth] = useState(currentMonth())
  const [year, setYear] = useState(currentYear())
  const [activeTab, setActiveTab] = useState<'monthly' | 'story'>('monthly')

  async function load() {
    setLoading(true)
    try {
      const [reportRes, trendRes] = await Promise.all([
        api.get('/reports/monthly', { params: { month, year } }),
        api.get('/dashboard/trends', { params: { months: 6 } }),
      ])
      setReport(reportRes.data)
      setTrends(trendRes.data.trends)
    } catch { toast.error('Failed to load reports') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [month, year])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <FileText size={20} className="text-teal-500" /> Financial Reports
          </h1>
          <p className="text-sm text-gray-500">Detailed analysis of your financial activity</p>
        </div>
        <div className="flex items-center gap-2">
          <select value={month} onChange={e => setMonth(Number(e.target.value))} className="input py-1.5 text-sm w-auto">
            {MONTH_NAMES.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
          </select>
          <select value={year} onChange={e => setYear(Number(e.target.value))} className="input py-1.5 text-sm w-auto">
            {[currentYear(), currentYear() - 1].map(y => <option key={y} value={y}>{y}</option>)}
          </select>
          <button onClick={downloadCSV}
            className="btn-secondary flex items-center gap-2 text-sm py-1.5">
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit">
        <button onClick={() => setActiveTab('monthly')}
          className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeTab === 'monthly' ? 'bg-white shadow-sm text-teal-600' : 'text-gray-500'}`}>
          Monthly Report
        </button>
        <button onClick={() => setActiveTab('story')}
          className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeTab === 'story' ? 'bg-white shadow-sm text-teal-600' : 'text-gray-500'}`}>
          <BookOpen size={14} className="inline mr-1" /> Financial Story
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : activeTab === 'story' ? (
        <div className="card">
          <h2 className="font-bold text-gray-800 mb-2 flex items-center gap-2">
            <BookOpen size={18} className="text-teal-500" />
            Your Financial Story — {report?.month_name} {year}
          </h2>
          <p className="text-base text-gray-700 leading-relaxed bg-teal-50 p-4 rounded-xl border border-teal-100">
            {report?.financial_story}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5">
            <div className="bg-green-50 rounded-xl p-3 text-center">
              <p className="text-xs text-gray-500">Income</p>
              <p className="font-bold text-green-700">{formatCurrency(report?.total_income ?? 0)}</p>
            </div>
            <div className="bg-red-50 rounded-xl p-3 text-center">
              <p className="text-xs text-gray-500">Expenses</p>
              <p className="font-bold text-red-600">{formatCurrency(report?.total_expenses ?? 0)}</p>
            </div>
            <div className="bg-teal-50 rounded-xl p-3 text-center">
              <p className="text-xs text-gray-500">Net Savings</p>
              <p className={`font-bold ${(report?.net_savings ?? 0) >= 0 ? 'text-teal-700' : 'text-red-600'}`}>
                {formatCurrency(report?.net_savings ?? 0)}
              </p>
            </div>
            <div className="bg-blue-50 rounded-xl p-3 text-center">
              <p className="text-xs text-gray-500">Savings Rate</p>
              <p className="font-bold text-blue-700">{report?.savings_rate?.toFixed(1)}%</p>
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="card text-center">
              <p className="text-xs text-gray-500">Total Income</p>
              <p className="text-lg font-bold text-green-600">{formatCurrency(report?.total_income ?? 0)}</p>
            </div>
            <div className="card text-center">
              <p className="text-xs text-gray-500">Total Expenses</p>
              <p className="text-lg font-bold text-red-500">{formatCurrency(report?.total_expenses ?? 0)}</p>
            </div>
            <div className="card text-center">
              <p className="text-xs text-gray-500">Net Savings</p>
              <p className={`text-lg font-bold ${(report?.net_savings ?? 0) >= 0 ? 'text-teal-600' : 'text-red-600'}`}>
                {formatCurrency(report?.net_savings ?? 0)}
              </p>
            </div>
            <div className="card text-center">
              <p className="text-xs text-gray-500">Savings Rate</p>
              <p className="text-lg font-bold text-blue-600">{report?.savings_rate?.toFixed(1)}%</p>
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">6-Month Trend</h3>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                  <YAxis tickFormatter={(v: number) => `₹${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v: unknown) => formatCurrency(Number(v))} />
                  <Legend />
                  <Line type="monotone" dataKey="income" name="Income" stroke="#22c55e" strokeWidth={2} />
                  <Line type="monotone" dataKey="expenses" name="Expenses" stroke="#ef4444" strokeWidth={2} />
                  <Line type="monotone" dataKey="savings" name="Savings" stroke="#427A76" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">Expense by Category</h3>
              {report?.expense_by_category && report.expense_by_category.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={160}>
                    <PieChart>
                      <Pie data={report.expense_by_category} dataKey="amount" nameKey="category"
                        cx="50%" cy="50%" innerRadius={40} outerRadius={70}>
                        {report.expense_by_category.map((_, i) => (
                          <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v: unknown) => formatCurrency(Number(v))} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-1 mt-2">
                    {report.expense_by_category.slice(0, 5).map((c, i) => (
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
                <div className="flex items-center justify-center h-40 text-gray-400 text-sm">No expense data</div>
              )}
            </div>
          </div>

          {/* Category tables */}
          {report && (report.income_by_category.length > 0 || report.expense_by_category.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="card">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Income Sources</h3>
                <div className="space-y-2">
                  {report.income_by_category.map(c => (
                    <div key={c.category} className="flex justify-between text-sm">
                      <span className="text-gray-600">{c.category}</span>
                      <span className="font-medium text-green-600">{formatCurrency(c.amount)}</span>
                    </div>
                  ))}
                  {report.income_by_category.length === 0 && (
                    <p className="text-xs text-gray-400">No income recorded</p>
                  )}
                </div>
              </div>
              <div className="card">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Expense Breakdown</h3>
                <div className="space-y-2">
                  {report.expense_by_category.map(c => (
                    <div key={c.category} className="flex justify-between text-sm">
                      <span className="text-gray-600">{c.category}</span>
                      <span className="font-medium text-red-500">{formatCurrency(c.amount)}</span>
                    </div>
                  ))}
                  {report.expense_by_category.length === 0 && (
                    <p className="text-xs text-gray-400">No expenses recorded</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
