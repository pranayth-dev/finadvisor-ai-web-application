import { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, X, Calendar, CheckCircle, AlertCircle, Bell } from 'lucide-react'
import api from '../services/api'
import type { Bill } from '../types'
import { formatCurrency, formatDate } from '../utils/formatters'
import toast from 'react-hot-toast'

const BILL_CATEGORIES = [
  'Utilities', 'Rent', 'Insurance', 'Subscriptions', 'Loans', 'Healthcare',
  'Education', 'Internet', 'Phone', 'Entertainment', 'Food', 'Transport', 'Other',
]
const FREQUENCIES = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'yearly', label: 'Yearly' },
  { value: 'one-time', label: 'One-time' },
]
const PAYMENT_METHODS = ['Net Banking', 'UPI', 'Credit Card', 'Debit Card', 'Cash', 'Auto-debit', 'Other']

interface BillForm {
  name: string
  amount: string
  category: string
  frequency: string
  due_day: string
  next_due_date: string
  auto_pay: boolean
  notes: string
  payment_method: string
}

const DEFAULT_FORM: BillForm = {
  name: '', amount: '', category: 'Utilities', frequency: 'monthly',
  due_day: '', next_due_date: '', auto_pay: false, notes: '', payment_method: 'Net Banking',
}

function BillModal({ initial, onSave, onClose }: {
  initial?: Bill | null
  onSave: (data: BillForm) => Promise<void>
  onClose: () => void
}) {
  const [form, setForm] = useState<BillForm>(
    initial ? {
      name: initial.name,
      amount: String(initial.amount),
      category: initial.category,
      frequency: initial.frequency,
      due_day: initial.due_day ? String(initial.due_day) : '',
      next_due_date: initial.next_due_date || '',
      auto_pay: initial.auto_pay,
      notes: initial.notes || '',
      payment_method: initial.payment_method || 'Net Banking',
    } : { ...DEFAULT_FORM }
  )
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  function set<K extends keyof BillForm>(key: K, val: BillForm[K]) {
    setForm(f => ({ ...f, [key]: val }))
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!form.name.trim()) { setError('Bill name is required'); return }
    if (!form.amount || Number(form.amount) <= 0) { setError('Enter a valid positive amount'); return }
    setSaving(true)
    try { await onSave(form) }
    catch (err: any) { setError(err.response?.data?.error || 'Failed to save') }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="font-bold text-gray-800">{initial ? 'Edit Bill' : 'Add Recurring Bill'}</h2>
          <button onClick={onClose}><X size={20} className="text-gray-400 hover:text-gray-600" /></button>
        </div>
        <form onSubmit={submit} className="p-5 space-y-4">
          {error && <p className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">{error}</p>}

          <div>
            <label className="label">Bill Name *</label>
            <input className="input" placeholder="e.g. Electricity Bill, Netflix…"
              value={form.name} onChange={e => set('name', e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Amount (₹) *</label>
              <input type="number" min="0.01" step="0.01" className="input"
                placeholder="0.00" value={form.amount}
                onChange={e => set('amount', e.target.value)} />
            </div>
            <div>
              <label className="label">Category</label>
              <select className="input" value={form.category} onChange={e => set('category', e.target.value)}>
                {BILL_CATEGORIES.map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Frequency</label>
              <select className="input" value={form.frequency} onChange={e => set('frequency', e.target.value)}>
                {FREQUENCIES.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
              </select>
            </div>
            {form.frequency === 'monthly' && (
              <div>
                <label className="label">Due Day (1–31)</label>
                <input type="number" min="1" max="31" className="input" placeholder="e.g. 5"
                  value={form.due_day} onChange={e => set('due_day', e.target.value)} />
              </div>
            )}
            {form.frequency !== 'monthly' && (
              <div>
                <label className="label">Next Due Date</label>
                <input type="date" className="input"
                  value={form.next_due_date} onChange={e => set('next_due_date', e.target.value)} />
              </div>
            )}
          </div>

          <div>
            <label className="label">Payment Method</label>
            <select className="input" value={form.payment_method} onChange={e => set('payment_method', e.target.value)}>
              {PAYMENT_METHODS.map(m => <option key={m}>{m}</option>)}
            </select>
          </div>

          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={form.auto_pay} onChange={e => set('auto_pay', e.target.checked)}
              className="w-4 h-4 accent-teal-500" />
            <span className="text-sm text-gray-600">Auto-pay enabled</span>
          </label>

          <div>
            <label className="label">Notes (optional)</label>
            <textarea className="input resize-none" rows={2}
              value={form.notes} onChange={e => set('notes', e.target.value)} />
          </div>

          <div className="flex gap-3 pt-1">
            <button type="submit" disabled={saving} className="btn-primary flex-1 py-2.5">
              {saving ? 'Saving…' : initial ? 'Update Bill' : 'Add Bill'}
            </button>
            <button type="button" onClick={onClose} className="btn-secondary px-5">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

function DaysUntilBadge({ bill }: { bill: Bill }) {
  if (!bill.next_due_date) return null
  const days = bill.days_until_due ?? 999
  if (bill.is_overdue) return (
    <span className="text-xs font-medium text-red-600 bg-red-50 px-2 py-0.5 rounded-full flex items-center gap-1">
      <AlertCircle size={10} /> Overdue {Math.abs(days)}d
    </span>
  )
  if (days <= 3) return (
    <span className="text-xs font-medium text-orange-600 bg-orange-50 px-2 py-0.5 rounded-full flex items-center gap-1">
      <Bell size={10} /> Due in {days}d
    </span>
  )
  if (days <= 7) return (
    <span className="text-xs font-medium text-yellow-600 bg-yellow-50 px-2 py-0.5 rounded-full">
      Due in {days}d
    </span>
  )
  return (
    <span className="text-xs text-gray-400">
      Due {formatDate(bill.next_due_date)}
    </span>
  )
}

export default function BillsPage() {
  const [bills, setBills] = useState<Bill[]>([])
  const [loading, setLoading] = useState(true)
  const [totalMonthly, setTotalMonthly] = useState(0)
  const [showModal, setShowModal] = useState(false)
  const [editBill, setEditBill] = useState<Bill | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [showInactive, setShowInactive] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const res = await api.get('/bills', { params: { include_inactive: showInactive } })
      setBills(res.data.bills)
      setTotalMonthly(res.data.total_monthly_estimated)
    } catch { toast.error('Failed to load bills') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [showInactive])

  async function handleSave(form: BillForm) {
    const payload: any = {
      name: form.name.trim(),
      amount: Number(form.amount),
      category: form.category,
      frequency: form.frequency,
      auto_pay: form.auto_pay,
      notes: form.notes,
      payment_method: form.payment_method,
    }
    if (form.frequency === 'monthly' && form.due_day) {
      payload.due_day = Number(form.due_day)
    }
    if (form.next_due_date) {
      payload.next_due_date = form.next_due_date
    }
    if (editBill) {
      await api.put(`/bills/${editBill.id}`, payload)
      toast.success('Bill updated')
    } else {
      await api.post('/bills', payload)
      toast.success('Bill added')
    }
    setShowModal(false)
    setEditBill(null)
    load()
  }

  async function handleMarkPaid(id: number) {
    try {
      await api.post(`/bills/${id}/mark-paid`)
      toast.success('Bill marked as paid, due date advanced')
      load()
    } catch { toast.error('Failed to mark as paid') }
  }

  async function handleDelete(id: number) {
    try {
      await api.delete(`/bills/${id}`)
      toast.success('Bill deleted')
      setDeleteId(null)
      load()
    } catch { toast.error('Failed to delete') }
  }

  const activeBills = bills.filter(b => b.is_active)
  const upcomingCount = activeBills.filter(b => b.days_until_due !== undefined && b.days_until_due <= 7).length
  const overdue = activeBills.filter(b => b.is_overdue)

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Bell size={20} className="text-teal-500" /> Bills & Recurring Payments
          </h1>
          <p className="text-sm text-gray-500">Track and manage your regular payments</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm text-gray-500 cursor-pointer">
            <input type="checkbox" checked={showInactive} onChange={e => setShowInactive(e.target.checked)}
              className="w-4 h-4 accent-teal-500" />
            Show inactive
          </label>
          <button onClick={() => { setEditBill(null); setShowModal(true) }}
            className="btn-primary flex items-center gap-2">
            <Plus size={16} /> Add Bill
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card text-center">
          <p className="text-xs text-gray-500 mb-1">Monthly Total</p>
          <p className="text-lg font-bold text-gray-800">{formatCurrency(totalMonthly)}</p>
          <p className="text-xs text-gray-400">estimated</p>
        </div>
        <div className="card text-center">
          <p className="text-xs text-gray-500 mb-1">Active Bills</p>
          <p className="text-lg font-bold text-gray-800">{activeBills.length}</p>
        </div>
        <div className="card text-center">
          <p className="text-xs text-gray-500 mb-1">Due This Week</p>
          <p className={`text-lg font-bold ${upcomingCount > 0 ? 'text-orange-600' : 'text-gray-800'}`}>
            {upcomingCount}
          </p>
        </div>
        <div className="card text-center">
          <p className="text-xs text-gray-500 mb-1">Overdue</p>
          <p className={`text-lg font-bold ${overdue.length > 0 ? 'text-red-600' : 'text-gray-800'}`}>
            {overdue.length}
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : bills.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-16 gap-4">
          <div className="w-16 h-16 bg-teal-50 rounded-full flex items-center justify-center">
            <Bell size={28} className="text-teal-400" />
          </div>
          <div className="text-center">
            <p className="font-medium text-gray-700 mb-1">No bills tracked yet</p>
            <p className="text-sm text-gray-400 mb-4">Add your recurring bills to track upcoming payments</p>
          </div>
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <Plus size={16} /> Add Your First Bill
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {bills.map(b => (
            <div key={b.id} className={`card ${!b.is_active ? 'opacity-60' : b.is_overdue ? 'border-red-200' : ''}`}>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-semibold text-gray-800">{b.name}</h3>
                    {!b.is_active && (
                      <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">Inactive</span>
                    )}
                    {b.auto_pay && (
                      <span className="text-xs text-green-600 bg-green-50 px-1.5 py-0.5 rounded">Auto-pay</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-xs text-gray-400 flex-wrap">
                    <span className="bg-gray-100 px-1.5 py-0.5 rounded">{b.category}</span>
                    <span className="capitalize">{b.frequency}</span>
                    {b.payment_method && <span>{b.payment_method}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <button onClick={() => { setEditBill(b); setShowModal(true) }}
                    className="w-7 h-7 flex items-center justify-center rounded hover:bg-teal-50 text-gray-400 hover:text-teal-600">
                    <Edit2 size={13} />
                  </button>
                  <button onClick={() => setDeleteId(b.id)}
                    className="w-7 h-7 flex items-center justify-center rounded hover:bg-red-50 text-gray-400 hover:text-red-500">
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between mt-2">
                <div>
                  <p className="text-lg font-bold text-gray-800">{formatCurrency(b.amount)}</p>
                  <DaysUntilBadge bill={b} />
                </div>
                {b.is_active && (
                  <button onClick={() => handleMarkPaid(b.id)}
                    className="flex items-center gap-1 text-xs font-medium text-teal-600 bg-teal-50 hover:bg-teal-100 px-3 py-1.5 rounded-lg transition-colors">
                    <CheckCircle size={13} /> Mark Paid
                  </button>
                )}
              </div>

              {b.notes && <p className="text-xs text-gray-400 mt-2 border-t pt-2">{b.notes}</p>}
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <BillModal initial={editBill} onSave={handleSave}
          onClose={() => { setShowModal(false); setEditBill(null) }} />
      )}

      {deleteId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl">
            <h3 className="font-bold text-gray-800 mb-2">Delete Bill</h3>
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
