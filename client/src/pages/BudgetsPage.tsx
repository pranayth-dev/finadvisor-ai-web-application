import { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, X, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react'
import api from '../services/api'
import type { Budget } from '../types'
import { formatCurrency, EXPENSE_CATEGORIES, MONTH_NAMES, currentMonth, currentYear } from '../utils/formatters'
import toast from 'react-hot-toast'

function BudgetModal({
  initial, month, year, onSave, onClose
}: {
  initial?: Budget | null
  month: number
  year: number
  onSave: (data: any) => Promise<void>
  onClose: () => void
}) {
  const [form, setForm] = useState({
    category: initial?.category || EXPENSE_CATEGORIES[0],
    limit_amount: initial?.limit_amount?.toString() || '',
    month: month,
    year: year,
    notes: initial?.notes || '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!form.limit_amount || Number(form.limit_amount) <= 0) {
      setError('Enter a valid positive limit amount')
      return
    }
    setSaving(true)
    try { await onSave({ ...form, limit_amount: Number(form.limit_amount) }) }
    catch (err: any) { setError(err.response?.data?.error || 'Failed to save') }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="font-bold text-gray-800">{initial ? 'Edit Budget' : 'Create Budget'}</h2>
          <button onClick={onClose}><X size={20} className="text-gray-400 hover:text-gray-600" /></button>
        </div>
        <form onSubmit={submit} className="p-5 space-y-4">
          {error && <p className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">{error}</p>}
          <div>
            <label className="label">Category</label>
            <select className="input" value={form.category}
              onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
              disabled={!!initial}>
              {EXPENSE_CATEGORIES.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Monthly Limit (₹)</label>
            <input type="number" min="1" step="1" className="input"
              placeholder="e.g. 5000"
              value={form.limit_amount}
              onChange={e => setForm(f => ({ ...f, limit_amount: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Month</label>
              <select className="input" value={form.month}
                onChange={e => setForm(f => ({ ...f, month: Number(e.target.value) }))}
                disabled={!!initial}>
                {MONTH_NAMES.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Year</label>
              <select className="input" value={form.year}
                onChange={e => setForm(f => ({ ...f, year: Number(e.target.value) }))}
                disabled={!!initial}>
                {[currentYear(), currentYear() - 1].map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="label">Notes (optional)</label>
            <input className="input" placeholder="Any notes…"
              value={form.notes}
              onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
          </div>
          <div className="flex gap-3 pt-1">
            <button type="submit" disabled={saving} className="btn-primary flex-1 py-2.5">
              {saving ? 'Saving…' : initial ? 'Update Budget' : 'Create Budget'}
            </button>
            <button type="button" onClick={onClose} className="btn-secondary px-5">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: Budget['status'] }) {
  if (status === 'over_budget') return (
    <span className="flex items-center gap-1 text-xs font-medium text-red-600 bg-red-50 px-2 py-0.5 rounded-full">
      <AlertTriangle size={11} /> Over Budget
    </span>
  )
  if (status === 'near_limit') return (
    <span className="flex items-center gap-1 text-xs font-medium text-orange-600 bg-orange-50 px-2 py-0.5 rounded-full">
      <AlertCircle size={11} /> Near Limit
    </span>
  )
  return (
    <span className="flex items-center gap-1 text-xs font-medium text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
      <CheckCircle size={11} /> Within Budget
    </span>
  )
}

export default function BudgetsPage() {
  const [budgets, setBudgets] = useState<Budget[]>([])
  const [loading, setLoading] = useState(true)
  const [month, setMonth] = useState(currentMonth())
  const [year, setYear] = useState(currentYear())
  const [showModal, setShowModal] = useState(false)
  const [editBudget, setEditBudget] = useState<Budget | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  async function load() {
    setLoading(true)
    try {
      const res = await api.get('/budgets', { params: { month, year } })
      setBudgets(res.data.budgets)
    } catch { toast.error('Failed to load budgets') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [month, year])

  async function handleSave(data: any) {
    if (editBudget) {
      await api.put(`/budgets/${editBudget.id}`, data)
      toast.success('Budget updated')
    } else {
      await api.post('/budgets', data)
      toast.success('Budget created')
    }
    setShowModal(false)
    setEditBudget(null)
    load()
  }

  async function handleDelete(id: number) {
    try {
      await api.delete(`/budgets/${id}`)
      toast.success('Budget deleted')
      setDeleteId(null)
      load()
    } catch { toast.error('Failed to delete') }
  }

  const totalBudget = budgets.reduce((s, b) => s + b.limit_amount, 0)
  const totalSpent = budgets.reduce((s, b) => s + b.spent, 0)

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Budgets</h1>
          <p className="text-sm text-gray-500">Set and track monthly spending limits</p>
        </div>
        <div className="flex items-center gap-2">
          <select value={month} onChange={e => setMonth(Number(e.target.value))} className="input py-1.5 text-sm w-auto">
            {MONTH_NAMES.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
          </select>
          <select value={year} onChange={e => setYear(Number(e.target.value))} className="input py-1.5 text-sm w-auto">
            {[currentYear(), currentYear() - 1].map(y => <option key={y} value={y}>{y}</option>)}
          </select>
          <button onClick={() => { setEditBudget(null); setShowModal(true) }}
            className="btn-primary flex items-center gap-2">
            <Plus size={16} /> Create Budget
          </button>
        </div>
      </div>

      {/* Summary cards */}
      {budgets.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card text-center">
            <p className="text-xs text-gray-500 mb-1">Total Budget</p>
            <p className="text-lg font-bold text-gray-800">{formatCurrency(totalBudget)}</p>
          </div>
          <div className="card text-center">
            <p className="text-xs text-gray-500 mb-1">Total Spent</p>
            <p className={`text-lg font-bold ${totalSpent > totalBudget ? 'text-red-600' : 'text-gray-800'}`}>
              {formatCurrency(totalSpent)}
            </p>
          </div>
          <div className="card text-center">
            <p className="text-xs text-gray-500 mb-1">Remaining</p>
            <p className={`text-lg font-bold ${totalBudget - totalSpent < 0 ? 'text-red-600' : 'text-green-600'}`}>
              {formatCurrency(totalBudget - totalSpent)}
            </p>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : budgets.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-16 gap-4">
          <div className="w-16 h-16 bg-teal-50 rounded-full flex items-center justify-center">
            <AlertCircle size={28} className="text-teal-400" />
          </div>
          <div className="text-center">
            <p className="font-medium text-gray-700 mb-1">No budgets for {MONTH_NAMES[month - 1]} {year}</p>
            <p className="text-sm text-gray-400 mb-4">Create budgets to track your spending limits</p>
          </div>
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <Plus size={16} /> Create Budget
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {budgets.map(b => (
            <div key={b.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-gray-800">{b.category}</h3>
                  <p className="text-xs text-gray-400">{MONTH_NAMES[month - 1]} {year}</p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={b.status} />
                  <button onClick={() => { setEditBudget(b); setShowModal(true) }}
                    className="w-7 h-7 flex items-center justify-center rounded hover:bg-teal-50 text-gray-400 hover:text-teal-600">
                    <Edit2 size={13} />
                  </button>
                  <button onClick={() => setDeleteId(b.id)}
                    className="w-7 h-7 flex items-center justify-center rounded hover:bg-red-50 text-gray-400 hover:text-red-500">
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
              <div className="mb-2">
                <div className="flex justify-between text-xs mb-1 text-gray-500">
                  <span>Spent: <span className="font-semibold text-gray-700">{formatCurrency(b.spent)}</span></span>
                  <span>Limit: <span className="font-semibold text-gray-700">{formatCurrency(b.limit_amount)}</span></span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      b.status === 'over_budget' ? 'bg-red-500'
                      : b.status === 'near_limit' ? 'bg-orange-400'
                      : 'bg-teal-500'
                    }`}
                    style={{ width: `${Math.min(100, b.utilization_percent)}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs mt-1.5 text-gray-500">
                  <span>{b.utilization_percent}% used</span>
                  <span className={b.remaining < 0 ? 'text-red-600 font-medium' : 'text-green-600 font-medium'}>
                    {b.remaining < 0 ? `₹${Math.abs(b.remaining).toLocaleString('en-IN')} over` : `₹${b.remaining.toLocaleString('en-IN')} left`}
                  </span>
                </div>
              </div>
              {b.notes && <p className="text-xs text-gray-400 mt-2 border-t pt-2">{b.notes}</p>}
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <BudgetModal
          initial={editBudget}
          month={month}
          year={year}
          onSave={handleSave}
          onClose={() => { setShowModal(false); setEditBudget(null) }}
        />
      )}

      {deleteId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl">
            <h3 className="font-bold text-gray-800 mb-2">Delete Budget</h3>
            <p className="text-sm text-gray-500 mb-5">Are you sure? This action cannot be undone.</p>
            <div className="flex gap-3">
              <button onClick={() => handleDelete(deleteId)} className="btn-danger flex-1">Delete</button>
              <button onClick={() => setDeleteId(null)} className="btn-secondary flex-1">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
