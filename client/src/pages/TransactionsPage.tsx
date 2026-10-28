import { useState, useEffect, useCallback } from 'react'
import { Plus, Search, Filter, Edit2, Trash2, X, ChevronDown, ChevronUp, Download } from 'lucide-react'
import api from '../services/api'
import type { Transaction } from '../types'
import {
  formatCurrency, formatDate, todayISO, EXPENSE_CATEGORIES,
  INCOME_CATEGORIES, PAYMENT_METHODS
} from '../utils/formatters'
import toast from 'react-hot-toast'

async function downloadCSV(startDate?: string, endDate?: string) {
  try {
    const params: Record<string, string> = {}
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    const res = await api.get('/reports/export', { params, responseType: 'blob' })
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

interface TxnFormState {
  description: string
  amount: string
  type: 'income' | 'expense'
  category: string
  date: string
  notes: string
  payment_method: string
}

const DEFAULT_FORM: TxnFormState = {
  description: '', amount: '', type: 'expense', category: 'Food',
  date: todayISO(), notes: '', payment_method: 'UPI',
}

function TransactionModal({
  initial, onSave, onClose
}: {
  initial?: Transaction | null
  onSave: (data: TxnFormState) => Promise<void>
  onClose: () => void
}) {
  const [form, setForm] = useState<TxnFormState>(
    initial
      ? { description: initial.description, amount: String(initial.amount), type: initial.type,
          category: initial.category, date: initial.date, notes: initial.notes || '', payment_method: initial.payment_method || 'UPI' }
      : { ...DEFAULT_FORM }
  )
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const categories = form.type === 'income' ? INCOME_CATEGORIES : EXPENSE_CATEGORIES

  function set(key: keyof TxnFormState, val: string) {
    setForm(f => {
      const next = { ...f, [key]: val }
      if (key === 'type') {
        next.category = val === 'income' ? 'Salary' : 'Food'
      }
      return next
    })
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const errs: Record<string, string> = {}
    if (!form.description.trim()) errs.description = 'Description is required'
    if (!form.amount || isNaN(Number(form.amount)) || Number(form.amount) <= 0) errs.amount = 'Enter a valid positive amount'
    if (!form.date) errs.date = 'Date is required'
    setErrors(errs)
    if (Object.keys(errs).length) return
    setSaving(true)
    try { await onSave(form) } finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="font-bold text-gray-800">{initial ? 'Edit Transaction' : 'Add Transaction'}</h2>
          <button onClick={onClose}><X size={20} className="text-gray-400 hover:text-gray-600" /></button>
        </div>
        <form onSubmit={submit} className="p-5 space-y-4">
          {/* Type toggle */}
          <div className="flex rounded-lg bg-gray-100 p-1">
            {(['expense', 'income'] as const).map(t => (
              <button key={t} type="button" onClick={() => set('type', t)}
                className={`flex-1 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  form.type === t ? (t === 'income' ? 'bg-green-500 text-white' : 'bg-red-500 text-white') : 'text-gray-500'
                }`}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>

          <div>
            <label className="label">Description *</label>
            <input className="input" placeholder="e.g. Monthly Salary" value={form.description}
              onChange={e => set('description', e.target.value)} />
            {errors.description && <p className="text-red-500 text-xs mt-1">{errors.description}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Amount (₹) *</label>
              <input type="number" min="0.01" step="0.01" className="input"
                placeholder="0.00" value={form.amount}
                onChange={e => set('amount', e.target.value)} />
              {errors.amount && <p className="text-red-500 text-xs mt-1">{errors.amount}</p>}
            </div>
            <div>
              <label className="label">Date *</label>
              <input type="date" className="input" value={form.date}
                onChange={e => set('date', e.target.value)} />
              {errors.date && <p className="text-red-500 text-xs mt-1">{errors.date}</p>}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Category</label>
              <select className="input" value={form.category} onChange={e => set('category', e.target.value)}>
                {categories.map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Payment Method</label>
              <select className="input" value={form.payment_method} onChange={e => set('payment_method', e.target.value)}>
                {PAYMENT_METHODS.map(m => <option key={m}>{m}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="label">Notes (optional)</label>
            <textarea className="input resize-none" rows={2} placeholder="Any additional notes…"
              value={form.notes} onChange={e => set('notes', e.target.value)} />
          </div>

          <div className="flex gap-3 pt-1">
            <button type="submit" disabled={saving} className="btn-primary flex-1 py-2.5">
              {saving ? 'Saving…' : initial ? 'Update Transaction' : 'Add Transaction'}
            </button>
            <button type="button" onClick={onClose} className="btn-secondary px-5">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [showModal, setShowModal] = useState(false)
  const [editTxn, setEditTxn] = useState<Transaction | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  // Filters
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [sortBy, setSortBy] = useState('date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [showFilters, setShowFilters] = useState(false)

  const PER_PAGE = 15

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.get('/transactions', {
        params: { page, per_page: PER_PAGE, search, type: typeFilter || undefined,
          category: categoryFilter || undefined, start_date: startDate || undefined,
          end_date: endDate || undefined, sort_by: sortBy, sort_order: sortOrder }
      })
      setTransactions(res.data.transactions)
      setTotal(res.data.total)
    } catch { toast.error('Failed to load transactions') }
    finally { setLoading(false) }
  }, [page, search, typeFilter, categoryFilter, startDate, endDate, sortBy, sortOrder])

  useEffect(() => { load() }, [load])
  useEffect(() => { setPage(1) }, [search, typeFilter, categoryFilter, startDate, endDate, sortBy, sortOrder])

  async function handleSave(form: TxnFormState) {
    try {
      if (editTxn) {
        await api.put(`/transactions/${editTxn.id}`, form)
        toast.success('Transaction updated')
      } else {
        await api.post('/transactions', form)
        toast.success('Transaction added')
      }
      setShowModal(false)
      setEditTxn(null)
      load()
    } catch (err: any) {
      const msgs = err.response?.data?.errors || [err.response?.data?.error || 'Failed']
      toast.error(msgs.join(', '))
      throw err
    }
  }

  async function handleDelete(id: number) {
    try {
      await api.delete(`/transactions/${id}`)
      toast.success('Transaction deleted')
      setDeleteId(null)
      load()
    } catch { toast.error('Failed to delete') }
  }

  function toggleSort(col: string) {
    if (sortBy === col) setSortOrder(o => o === 'asc' ? 'desc' : 'asc')
    else { setSortBy(col); setSortOrder('desc') }
  }

  const totalPages = Math.ceil(total / PER_PAGE)

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Transactions</h1>
          <p className="text-sm text-gray-500">{total} transaction{total !== 1 ? 's' : ''} found</p>
        </div>
        <button onClick={() => { setEditTxn(null); setShowModal(true) }}
          className="btn-primary flex items-center gap-2">
          <Plus size={16} /> Add Transaction
        </button>
      </div>

      {/* Search & Filters */}
      <div className="card space-y-3">
        <div className="flex gap-2 flex-wrap">
          <div className="relative flex-1 min-w-[180px]">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="input pl-8" placeholder="Search transactions…" value={search}
              onChange={e => setSearch(e.target.value)} />
          </div>
          <select className="input py-2 text-sm w-auto" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
            <option value="">All Types</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
          <button onClick={() => setShowFilters(!showFilters)}
            className={`btn-secondary flex items-center gap-1 text-sm ${showFilters ? 'bg-teal-50 border-teal-300' : ''}`}>
            <Filter size={14} /> Filters {showFilters ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          <button onClick={() => downloadCSV(startDate, endDate)}
            className="btn-secondary flex items-center gap-1 text-sm">
            <Download size={14} /> Export CSV
          </button>
        </div>

        {showFilters && (
          <div className="flex gap-3 flex-wrap pt-1 border-t border-gray-100">
            <div>
              <label className="label text-xs">Category</label>
              <select className="input py-1.5 text-sm w-auto" value={categoryFilter}
                onChange={e => setCategoryFilter(e.target.value)}>
                <option value="">All Categories</option>
                {[...INCOME_CATEGORIES, ...EXPENSE_CATEGORIES].map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="label text-xs">From</label>
              <input type="date" className="input py-1.5 text-sm" value={startDate}
                onChange={e => setStartDate(e.target.value)} />
            </div>
            <div>
              <label className="label text-xs">To</label>
              <input type="date" className="input py-1.5 text-sm" value={endDate}
                onChange={e => setEndDate(e.target.value)} />
            </div>
            <button onClick={() => { setSearch(''); setTypeFilter(''); setCategoryFilter(''); setStartDate(''); setEndDate('') }}
              className="text-xs text-gray-500 hover:text-red-500 self-end pb-2">Clear all</button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="card overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Description
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none"
                onClick={() => toggleSort('date')}>
                <span className="flex items-center gap-1">
                  Date {sortBy === 'date' && (sortOrder === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
                </span>
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Category</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Payment</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none"
                onClick={() => toggleSort('amount')}>
                <span className="flex items-center justify-end gap-1">
                  Amount {sortBy === 'amount' && (sortOrder === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
                </span>
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {loading ? (
              <tr><td colSpan={6} className="text-center py-10 text-gray-400">Loading…</td></tr>
            ) : transactions.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-14">
                  <p className="text-gray-400 mb-3">No transactions found</p>
                  <button onClick={() => { setEditTxn(null); setShowModal(true) }}
                    className="btn-primary text-sm py-1.5 px-4">
                    Add your first transaction
                  </button>
                </td>
              </tr>
            ) : transactions.map(t => (
              <tr key={t.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${
                      t.type === 'income' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                    }`}>
                      {t.category[0]}
                    </div>
                    <div>
                      <p className="font-medium text-gray-800 truncate max-w-[180px]">{t.description}</p>
                      {t.notes && <p className="text-xs text-gray-400 truncate max-w-[180px]">{t.notes}</p>}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{formatDate(t.date)}</td>
                <td className="px-4 py-3">
                  <span className="badge-blue">{t.category}</span>
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">{t.payment_method}</td>
                <td className={`px-4 py-3 text-right font-semibold whitespace-nowrap ${
                  t.type === 'income' ? 'text-green-600' : 'text-red-500'
                }`}>
                  {t.type === 'income' ? '+' : '-'}{formatCurrency(t.amount)}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button onClick={() => { setEditTxn(t); setShowModal(true) }}
                      className="w-7 h-7 flex items-center justify-center rounded hover:bg-teal-50 text-gray-400 hover:text-teal-600">
                      <Edit2 size={14} />
                    </button>
                    <button onClick={() => setDeleteId(t.id)}
                      className="w-7 h-7 flex items-center justify-center rounded hover:bg-red-50 text-gray-400 hover:text-red-500">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Showing {(page - 1) * PER_PAGE + 1}–{Math.min(page * PER_PAGE, total)} of {total}
          </p>
          <div className="flex gap-1">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
              className="btn-secondary text-sm py-1 px-3 disabled:opacity-50">Prev</button>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
              className="btn-secondary text-sm py-1 px-3 disabled:opacity-50">Next</button>
          </div>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <TransactionModal
          initial={editTxn}
          onSave={handleSave}
          onClose={() => { setShowModal(false); setEditTxn(null) }}
        />
      )}

      {/* Delete confirmation */}
      {deleteId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl">
            <h3 className="font-bold text-gray-800 mb-2">Delete Transaction</h3>
            <p className="text-sm text-gray-500 mb-5">
              Are you sure you want to delete this transaction? This action cannot be undone.
            </p>
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
