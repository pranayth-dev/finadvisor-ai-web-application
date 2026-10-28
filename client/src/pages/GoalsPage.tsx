import { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, X, Target, Calendar, TrendingUp } from 'lucide-react'
import api from '../services/api'
import type { SavingsGoal } from '../types'
import { formatCurrency, todayISO, GOAL_CATEGORIES } from '../utils/formatters'
import toast from 'react-hot-toast'

function GoalModal({
  initial, onSave, onClose
}: {
  initial?: SavingsGoal | null
  onSave: (data: any) => Promise<void>
  onClose: () => void
}) {
  const [form, setForm] = useState({
    name: initial?.name || '',
    target_amount: initial?.target_amount?.toString() || '',
    current_amount: initial?.current_amount?.toString() || '0',
    target_date: initial?.target_date || '',
    category: initial?.category || 'Other',
    notes: initial?.notes || '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!form.name.trim()) { setError('Goal name is required'); return }
    if (!form.target_amount || Number(form.target_amount) <= 0) { setError('Enter a valid target amount'); return }
    setSaving(true)
    try {
      await onSave({
        name: form.name,
        target_amount: Number(form.target_amount),
        current_amount: Number(form.current_amount) || 0,
        target_date: form.target_date || null,
        category: form.category,
        notes: form.notes,
      })
    } catch (err: any) { setError(err.response?.data?.error || 'Failed to save') }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="font-bold text-gray-800">{initial ? 'Edit Goal' : 'Create Savings Goal'}</h2>
          <button onClick={onClose}><X size={20} className="text-gray-400 hover:text-gray-600" /></button>
        </div>
        <form onSubmit={submit} className="p-5 space-y-4">
          {error && <p className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">{error}</p>}
          <div>
            <label className="label">Goal Name *</label>
            <input className="input" placeholder="e.g. Emergency Fund, New Laptop…"
              value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          </div>
          <div>
            <label className="label">Category</label>
            <select className="input" value={form.category}
              onChange={e => setForm(f => ({ ...f, category: e.target.value }))}>
              {GOAL_CATEGORIES.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Target Amount (₹) *</label>
              <input type="number" min="1" className="input" placeholder="100000"
                value={form.target_amount}
                onChange={e => setForm(f => ({ ...f, target_amount: e.target.value }))} />
            </div>
            <div>
              <label className="label">Amount Saved (₹)</label>
              <input type="number" min="0" className="input" placeholder="0"
                value={form.current_amount}
                onChange={e => setForm(f => ({ ...f, current_amount: e.target.value }))} />
            </div>
          </div>
          <div>
            <label className="label">Target Date (optional)</label>
            <input type="date" className="input" min={todayISO()}
              value={form.target_date}
              onChange={e => setForm(f => ({ ...f, target_date: e.target.value }))} />
          </div>
          <div>
            <label className="label">Notes (optional)</label>
            <textarea className="input resize-none" rows={2}
              value={form.notes}
              onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
          </div>
          <div className="flex gap-3 pt-1">
            <button type="submit" disabled={saving} className="btn-primary flex-1 py-2.5">
              {saving ? 'Saving…' : initial ? 'Update Goal' : 'Create Goal'}
            </button>
            <button type="button" onClick={onClose} className="btn-secondary px-5">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function GoalsPage() {
  const [goals, setGoals] = useState<SavingsGoal[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editGoal, setEditGoal] = useState<SavingsGoal | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [showCompleted, setShowCompleted] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const res = await api.get('/goals', { params: { include_completed: showCompleted } })
      setGoals(res.data.goals)
    } catch { toast.error('Failed to load goals') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [showCompleted])

  async function handleSave(data: any) {
    if (editGoal) {
      await api.put(`/goals/${editGoal.id}`, data)
      toast.success('Goal updated')
    } else {
      await api.post('/goals', data)
      toast.success('Goal created')
    }
    setShowModal(false)
    setEditGoal(null)
    load()
  }

  async function handleDelete(id: number) {
    try {
      await api.delete(`/goals/${id}`)
      toast.success('Goal deleted')
      setDeleteId(null)
      load()
    } catch { toast.error('Failed to delete') }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Savings Goals</h1>
          <p className="text-sm text-gray-500">Track your financial milestones</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm text-gray-500 cursor-pointer">
            <input type="checkbox" checked={showCompleted}
              onChange={e => setShowCompleted(e.target.checked)}
              className="w-4 h-4 accent-teal-500" />
            Show completed
          </label>
          <button onClick={() => { setEditGoal(null); setShowModal(true) }}
            className="btn-primary flex items-center gap-2">
            <Plus size={16} /> New Goal
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : goals.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-16 gap-4">
          <div className="w-16 h-16 bg-teal-50 rounded-full flex items-center justify-center">
            <Target size={28} className="text-teal-400" />
          </div>
          <div className="text-center">
            <p className="font-medium text-gray-700 mb-1">No savings goals yet</p>
            <p className="text-sm text-gray-400 mb-4">Create a goal to track your savings progress</p>
          </div>
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <Plus size={16} /> Create Your First Goal
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {goals.map(g => (
            <div key={g.id} className={`card ${g.is_completed ? 'border-green-200 bg-green-50' : ''}`}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-teal-100 rounded-xl flex items-center justify-center">
                    <Target size={18} className="text-teal-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-800">{g.name}</h3>
                    <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{g.category}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {g.is_completed && (
                    <span className="text-xs font-medium text-green-700 bg-green-100 px-2 py-0.5 rounded-full mr-1">
                      ✓ Completed
                    </span>
                  )}
                  <button onClick={() => { setEditGoal(g); setShowModal(true) }}
                    className="w-7 h-7 flex items-center justify-center rounded hover:bg-teal-50 text-gray-400 hover:text-teal-600">
                    <Edit2 size={13} />
                  </button>
                  <button onClick={() => setDeleteId(g.id)}
                    className="w-7 h-7 flex items-center justify-center rounded hover:bg-red-50 text-gray-400 hover:text-red-500">
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>

              {/* Progress */}
              <div className="mb-3">
                <div className="flex justify-between text-xs mb-1 text-gray-500">
                  <span>Progress: <span className="font-semibold text-teal-600">{g.progress_percent}%</span></span>
                  <span>{formatCurrency(g.current_amount)} / {formatCurrency(g.target_amount)}</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${g.is_completed ? 'bg-green-500' : 'bg-teal-500'}`}
                    style={{ width: `${g.progress_percent}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {formatCurrency(g.remaining_amount)} remaining
                </p>
              </div>

              {/* Details */}
              <div className="flex flex-wrap gap-3 text-xs text-gray-500 border-t pt-2">
                {g.target_date && (
                  <span className="flex items-center gap-1">
                    <Calendar size={11} />
                    Target: {new Date(g.target_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                  </span>
                )}
                {g.monthly_needed && (
                  <span className="flex items-center gap-1 text-teal-600 font-medium">
                    <TrendingUp size={11} />
                    Save {formatCurrency(g.monthly_needed)}/mo
                  </span>
                )}
              </div>
              {g.notes && <p className="text-xs text-gray-400 mt-2">{g.notes}</p>}
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <GoalModal
          initial={editGoal}
          onSave={handleSave}
          onClose={() => { setShowModal(false); setEditGoal(null) }}
        />
      )}

      {deleteId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl">
            <h3 className="font-bold text-gray-800 mb-2">Delete Goal</h3>
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
