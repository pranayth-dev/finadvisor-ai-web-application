import { useState, useEffect, useCallback } from 'react'
import {
  Users, Plus, TrendingUp, TrendingDown, Target, UserPlus, UserMinus,
  Mail, CheckCircle, XCircle, PiggyBank, Trash2, RefreshCw,
  DollarSign, BarChart2, Clock, LogOut,
} from 'lucide-react'
import api from '../services/api'
import { useAuth } from '../hooks/useAuth'
import { formatCurrency, MONTH_NAMES, currentMonth, currentYear } from '../utils/formatters'
import toast from 'react-hot-toast'

// ─── Types ───────────────────────────────────────────────────────────────────

interface FamilyMember {
  id: number
  name: string
  email: string
  is_owner: boolean
}

interface FamilyInvitation {
  id: number
  group_id: number
  invited_email: string
  invited_by: number
  status: string
  group_name?: string
  invited_by_name?: string
}

interface FamilyGoal {
  id: number
  group_id: number
  name: string
  target_amount: number
  current_amount: number
  remaining_amount: number
  progress_percent: number
  target_date?: string
  category: string
  is_completed: boolean
  monthly_needed?: number
}

interface FamilyData {
  id: number
  name: string
  description?: string
  created_by: number
  is_owner: boolean
  members: FamilyMember[]
  pending_invitations?: FamilyInvitation[]
}

interface FamilyOverview {
  combined_income: number
  combined_expenses: number
  net_savings: number
  savings_rate: number
  month: number
  year: number
  members: { member: { id: number; name: string }; income: number; expenses: number }[]
  goals: FamilyGoal[]
  recent_transactions: any[]
  category_spending: { category: string; amount: number }[]
}

// ─── Goal Form ───────────────────────────────────────────────────────────────

function GoalForm({
  groupId,
  onCreated,
  onCancel,
}: {
  groupId: number
  onCreated: () => void
  onCancel: () => void
}) {
  const [name, setName] = useState('')
  const [target, setTarget] = useState('')
  const [current, setCurrent] = useState('0')
  const [targetDate, setTargetDate] = useState('')
  const [category, setCategory] = useState('Other')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || !target) { toast.error('Name and target amount are required'); return }
    setSaving(true)
    try {
      await api.post('/family/goals', {
        name: name.trim(),
        target_amount: parseFloat(target),
        current_amount: parseFloat(current || '0'),
        target_date: targetDate || null,
        category,
      })
      toast.success('Family goal created!')
      onCreated()
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to create goal')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-3">
      <h4 className="font-semibold text-gray-800 text-sm">New Shared Goal</h4>
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="label">Goal Name *</label>
          <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Family Vacation" required />
        </div>
        <div>
          <label className="label">Target Amount (₹) *</label>
          <input className="input" type="number" min="1" step="0.01" value={target} onChange={e => setTarget(e.target.value)} placeholder="50000" required />
        </div>
        <div>
          <label className="label">Already Saved (₹)</label>
          <input className="input" type="number" min="0" step="0.01" value={current} onChange={e => setCurrent(e.target.value)} placeholder="0" />
        </div>
        <div>
          <label className="label">Target Date</label>
          <input className="input" type="date" value={targetDate} onChange={e => setTargetDate(e.target.value)} />
        </div>
        <div>
          <label className="label">Category</label>
          <select className="input" value={category} onChange={e => setCategory(e.target.value)}>
            {['Other', 'Travel', 'Emergency', 'Education', 'Housing', 'Vehicle', 'Electronics', 'Healthcare'].map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="flex gap-2">
        <button type="submit" disabled={saving} className="btn-primary text-sm px-4">
          {saving ? 'Saving…' : 'Create Goal'}
        </button>
        <button type="button" onClick={onCancel} className="btn-secondary text-sm px-4">Cancel</button>
      </div>
    </form>
  )
}

// ─── Goal Card ────────────────────────────────────────────────────────────────

function GoalCard({
  goal,
  isOwner,
  onContribute,
  onDelete,
}: {
  goal: FamilyGoal
  isOwner: boolean
  onContribute: (id: number, amount: number) => void
  onDelete: (id: number) => void
}) {
  const [showContrib, setShowContrib] = useState(false)
  const [amount, setAmount] = useState('')

  function handleContrib(e: React.FormEvent) {
    e.preventDefault()
    const val = parseFloat(amount)
    if (!val || val <= 0) { toast.error('Enter a valid amount'); return }
    onContribute(goal.id, val)
    setAmount('')
    setShowContrib(false)
  }

  const progressColor =
    goal.progress_percent >= 100 ? 'bg-green-500'
    : goal.progress_percent >= 75 ? 'bg-teal-500'
    : goal.progress_percent >= 50 ? 'bg-blue-500'
    : 'bg-orange-400'

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <h4 className="font-semibold text-gray-800 text-sm">{goal.name}</h4>
          <p className="text-xs text-gray-400">{goal.category}{goal.target_date ? ` · Due ${goal.target_date}` : ''}</p>
        </div>
        {goal.is_completed && (
          <span className="badge-green text-xs">Completed</span>
        )}
      </div>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>{formatCurrency(goal.current_amount)} saved</span>
          <span>{goal.progress_percent.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full transition-all ${progressColor}`}
            style={{ width: `${Math.min(100, goal.progress_percent)}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>Target: {formatCurrency(goal.target_amount)}</span>
          <span>Remaining: {formatCurrency(goal.remaining_amount)}</span>
        </div>
      </div>

      {goal.monthly_needed && !goal.is_completed && (
        <p className="text-xs text-teal-600 mb-3">
          Save {formatCurrency(goal.monthly_needed)}/month to reach this goal on time.
        </p>
      )}

      {/* Actions */}
      {!goal.is_completed && (
        <div className="flex items-center gap-2">
          {!showContrib ? (
            <button
              onClick={() => setShowContrib(true)}
              className="flex items-center gap-1 text-xs font-medium text-teal-600 hover:text-teal-700"
            >
              <PiggyBank size={13} /> Add Contribution
            </button>
          ) : (
            <form onSubmit={handleContrib} className="flex gap-1.5 items-center flex-1">
              <input
                className="input text-xs py-1 flex-1"
                type="number"
                min="1"
                step="0.01"
                placeholder="Amount ₹"
                value={amount}
                onChange={e => setAmount(e.target.value)}
                autoFocus
              />
              <button type="submit" className="btn-primary text-xs py-1 px-3">Add</button>
              <button type="button" onClick={() => setShowContrib(false)} className="text-xs text-gray-400 hover:text-gray-600">Cancel</button>
            </form>
          )}
          {isOwner && (
            <button
              onClick={() => onDelete(goal.id)}
              className="ml-auto text-xs text-gray-400 hover:text-red-500 transition-colors"
            >
              <Trash2 size={13} />
            </button>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function FamilyPage() {
  const { user, updateUser } = useAuth()
  const [family, setFamily] = useState<FamilyData | null>(null)
  const [overview, setOverview] = useState<FamilyOverview | null>(null)
  const [goals, setGoals] = useState<FamilyGoal[]>([])
  const [myInvitations, setMyInvitations] = useState<FamilyInvitation[]>([])
  const [loading, setLoading] = useState(true)
  const [month, setMonth] = useState(currentMonth())
  const [year, setYear] = useState(currentYear())
  const [showCreate, setShowCreate] = useState(false)
  const [groupName, setGroupName] = useState('')
  const [groupDesc, setGroupDesc] = useState('')
  const [creating, setCreating] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviting, setInviting] = useState(false)
  const [showGoalForm, setShowGoalForm] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'goals' | 'members' | 'transactions'>('overview')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [familyRes, invRes] = await Promise.all([
        api.get('/family'),
        api.get('/family/my-invitations'),
      ])
      setFamily(familyRes.data.family)
      setMyInvitations(invRes.data.invitations || [])

      if (familyRes.data.family) {
        const [ovRes, goalsRes] = await Promise.all([
          api.get('/family/overview', { params: { month, year } }),
          api.get('/family/goals'),
        ])
        setOverview(ovRes.data)
        setGoals(goalsRes.data.goals || [])
      }
    } catch {
      toast.error('Failed to load family data')
    } finally {
      setLoading(false)
    }
  }, [month, year])

  useEffect(() => { load() }, [load])

  async function createFamily(e: React.FormEvent) {
    e.preventDefault()
    if (!groupName.trim()) { toast.error('Group name is required'); return }
    setCreating(true)
    try {
      const res = await api.post('/family/create', { name: groupName, description: groupDesc })
      setFamily(res.data.family)
      const profileRes = await api.get('/auth/me')
      updateUser(profileRes.data.user)
      toast.success('Family group created!')
      setShowCreate(false)
      setGroupName('')
      setGroupDesc('')
      load()
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to create group')
    } finally {
      setCreating(false) }
  }

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault()
    if (!inviteEmail.trim()) return
    setInviting(true)
    try {
      await api.post('/family/invite', { email: inviteEmail.trim() })
      toast.success(`Invitation sent to ${inviteEmail}`)
      setInviteEmail('')
      load()
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to send invitation')
    } finally {
      setInviting(false)
    }
  }

  async function respondInvitation(id: number, action: 'accept' | 'reject') {
    try {
      const res = await api.post(`/family/invitations/${id}/respond`, { action })
      toast.success(res.data.message)
      const profileRes = await api.get('/auth/me')
      updateUser(profileRes.data.user)
      load()
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to respond to invitation')
    }
  }

  async function removeMember(memberId: number, name: string) {
    if (!confirm(`Remove ${name} from the family group?`)) return
    try {
      await api.delete(`/family/members/${memberId}`)
      toast.success(`${name} removed`)
      load()
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to remove member')
    }
  }

  async function leaveGroup() {
    if (!confirm('Are you sure you want to leave the family group?')) return
    try {
      await api.post('/family/leave')
      toast.success('Left family group')
      setFamily(null)
      setOverview(null)
      const profileRes = await api.get('/auth/me')
      updateUser(profileRes.data.user)
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to leave group')
    }
  }

  async function contributeGoal(goalId: number, amount: number) {
    try {
      const res = await api.post(`/family/goals/${goalId}/contribute`, { amount })
      toast.success(res.data.message)
      load()
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to add contribution')
    }
  }

  async function deleteGoal(goalId: number) {
    if (!confirm('Delete this shared goal?')) return
    try {
      await api.delete(`/family/goals/${goalId}`)
      toast.success('Goal deleted')
      load()
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to delete goal')
    }
  }

  if (loading) return (
    <div className="flex justify-center py-20">
      <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  // ── Pending invitation banner ──────────────────────────────────────────────
  const invitationBanner = myInvitations.length > 0 && !family && (
    <div className="space-y-3">
      {myInvitations.map(inv => (
        <div key={inv.id} className="bg-teal-50 border border-teal-200 rounded-xl p-4 flex items-center gap-3 flex-wrap">
          <Mail size={18} className="text-teal-600 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-teal-800 text-sm">
              You've been invited to join <strong>{inv.group_name}</strong>
            </p>
            <p className="text-xs text-teal-600">Invited by {inv.invited_by_name}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => respondInvitation(inv.id, 'accept')}
              className="flex items-center gap-1 px-3 py-1.5 bg-teal-600 text-white text-xs font-semibold rounded-lg hover:bg-teal-700"
            >
              <CheckCircle size={13} /> Accept
            </button>
            <button
              onClick={() => respondInvitation(inv.id, 'reject')}
              className="flex items-center gap-1 px-3 py-1.5 border border-gray-200 text-gray-600 text-xs font-semibold rounded-lg hover:border-red-300 hover:text-red-600"
            >
              <XCircle size={13} /> Decline
            </button>
          </div>
        </div>
      ))}
    </div>
  )

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Users size={20} className="text-teal-500" /> Family Finance
          </h1>
          <p className="text-sm text-gray-500">Track shared household finances</p>
        </div>
        {family && (
          <div className="flex gap-2">
            <button
              onClick={() => load()}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-200 text-sm text-gray-600 rounded-lg hover:border-teal-300 hover:text-teal-600"
            >
              <RefreshCw size={14} /> Refresh
            </button>
            <button
              onClick={leaveGroup}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-red-200 text-sm text-red-600 rounded-lg hover:bg-red-50"
            >
              <LogOut size={14} /> Leave Group
            </button>
          </div>
        )}
      </div>

      {/* Invitation banners */}
      {invitationBanner}

      {/* No group — create or show invitation info */}
      {!family ? (
        <div className="card flex flex-col items-center justify-center py-16 gap-4">
          <div className="w-16 h-16 bg-teal-50 rounded-full flex items-center justify-center">
            <Users size={28} className="text-teal-400" />
          </div>
          <div className="text-center">
            <p className="font-medium text-gray-700 mb-1">No Family Group</p>
            <p className="text-sm text-gray-400 mb-4">
              Create a family group to track shared finances, or accept an invitation from a group owner.
            </p>
          </div>
          {showCreate ? (
            <form onSubmit={createFamily} className="w-full max-w-sm space-y-3">
              <input
                className="input"
                placeholder="Family group name *"
                value={groupName}
                onChange={e => setGroupName(e.target.value)}
                autoFocus
                required
              />
              <input
                className="input"
                placeholder="Description (optional)"
                value={groupDesc}
                onChange={e => setGroupDesc(e.target.value)}
              />
              <div className="flex gap-2">
                <button type="submit" disabled={creating} className="btn-primary flex-1">
                  {creating ? 'Creating…' : 'Create Group'}
                </button>
                <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary px-4">Cancel</button>
              </div>
            </form>
          ) : (
            <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
              <Plus size={16} /> Create Family Group
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Group header card */}
          <div className="card bg-teal-600 text-white">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center">
                <Users size={24} />
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-bold">{family.name}</h2>
                <p className="text-teal-200 text-sm">{family.members?.length || 1} member(s)</p>
                {family.description && <p className="text-teal-100 text-xs mt-0.5">{family.description}</p>}
              </div>
            </div>
          </div>

          {/* Month / year selector */}
          <div className="flex items-center gap-2">
            <select value={month} onChange={e => setMonth(Number(e.target.value))} className="input py-1.5 text-sm w-auto">
              {MONTH_NAMES.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
            </select>
            <select value={year} onChange={e => setYear(Number(e.target.value))} className="input py-1.5 text-sm w-auto">
              {[currentYear(), currentYear() - 1].map(y => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 bg-gray-100 p-1 rounded-lg overflow-x-auto">
            {[
              { id: 'overview', label: 'Overview', icon: BarChart2 },
              { id: 'goals', label: `Goals (${goals.filter(g => !g.is_completed).length})`, icon: Target },
              { id: 'members', label: 'Members', icon: Users },
              { id: 'transactions', label: 'Transactions', icon: DollarSign },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
                  activeTab === id
                    ? 'bg-white shadow-sm text-teal-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <Icon size={14} /> {label}
              </button>
            ))}
          </div>

          {/* ── Overview tab ── */}
          {activeTab === 'overview' && overview && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="card text-center">
                  <TrendingUp size={16} className="text-green-500 mx-auto mb-1" />
                  <p className="text-xs text-gray-500">Combined Income</p>
                  <p className="text-lg font-bold text-green-600">{formatCurrency(overview.combined_income)}</p>
                </div>
                <div className="card text-center">
                  <TrendingDown size={16} className="text-red-500 mx-auto mb-1" />
                  <p className="text-xs text-gray-500">Combined Expenses</p>
                  <p className="text-lg font-bold text-red-500">{formatCurrency(overview.combined_expenses)}</p>
                </div>
                <div className="card text-center">
                  <PiggyBank size={16} className="text-teal-500 mx-auto mb-1" />
                  <p className="text-xs text-gray-500">Net Savings</p>
                  <p className={`text-lg font-bold ${overview.net_savings >= 0 ? 'text-teal-600' : 'text-red-600'}`}>
                    {formatCurrency(overview.net_savings)}
                  </p>
                </div>
              </div>

              {/* Member breakdown */}
              <div className="card">
                <h3 className="font-semibold text-gray-800 mb-3 text-sm">Member Contributions</h3>
                <div className="space-y-2">
                  {overview.members?.map(m => (
                    <div key={m.member.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-teal-500 rounded-full flex items-center justify-center text-white font-bold text-xs">
                          {m.member.name[0]}
                        </div>
                        <span className="font-medium text-gray-700 text-sm">{m.member.name}</span>
                      </div>
                      <div className="flex gap-4 text-xs">
                        <span className="text-green-600 font-medium">{formatCurrency(m.income)}</span>
                        <span className="text-red-500 font-medium">{formatCurrency(m.expenses)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Category spending */}
              {overview.category_spending.length > 0 && (
                <div className="card">
                  <h3 className="font-semibold text-gray-800 mb-3 text-sm">Spending by Category</h3>
                  <div className="space-y-2">
                    {overview.category_spending.slice(0, 5).map(c => (
                      <div key={c.category} className="flex items-center gap-2 text-sm">
                        <span className="text-gray-600 w-28 truncate">{c.category}</span>
                        <div className="flex-1 bg-gray-100 rounded-full h-2">
                          <div
                            className="h-2 bg-teal-500 rounded-full"
                            style={{ width: `${Math.min(100, c.amount / overview.combined_expenses * 100)}%` }}
                          />
                        </div>
                        <span className="font-medium text-gray-700 text-xs">{formatCurrency(c.amount)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recent transactions */}
              {overview.recent_transactions?.length > 0 && (
                <div className="card">
                  <h3 className="font-semibold text-gray-800 mb-3 text-sm">Recent Transactions</h3>
                  <div className="space-y-2">
                    {overview.recent_transactions.slice(0, 5).map((t: any) => (
                      <div key={t.id} className="flex items-center justify-between text-sm">
                        <div>
                          <p className="font-medium text-gray-700">{t.description}</p>
                          <p className="text-xs text-gray-400">{t.member_name} · {t.date}</p>
                        </div>
                        <span className={`font-semibold ${t.type === 'income' ? 'text-green-600' : 'text-red-500'}`}>
                          {t.type === 'income' ? '+' : '-'}{formatCurrency(t.amount)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Goals tab ── */}
          {activeTab === 'goals' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-800">Shared Savings Goals</h3>
                <button
                  onClick={() => setShowGoalForm(true)}
                  className="flex items-center gap-1.5 btn-primary text-sm"
                >
                  <Plus size={14} /> New Goal
                </button>
              </div>

              {showGoalForm && (
                <GoalForm
                  groupId={family.id}
                  onCreated={() => { setShowGoalForm(false); load() }}
                  onCancel={() => setShowGoalForm(false)}
                />
              )}

              {goals.length === 0 && !showGoalForm && (
                <div className="card flex flex-col items-center justify-center py-10 gap-3">
                  <Target size={28} className="text-teal-400" />
                  <p className="text-sm text-gray-500">No shared goals yet. Create one to start saving together.</p>
                </div>
              )}

              {goals.filter(g => !g.is_completed).map(g => (
                <GoalCard
                  key={g.id}
                  goal={g}
                  isOwner={!!family.is_owner}
                  onContribute={contributeGoal}
                  onDelete={deleteGoal}
                />
              ))}

              {goals.filter(g => g.is_completed).length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Completed</p>
                  {goals.filter(g => g.is_completed).map(g => (
                    <GoalCard
                      key={g.id}
                      goal={g}
                      isOwner={!!family.is_owner}
                      onContribute={contributeGoal}
                      onDelete={deleteGoal}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── Members tab ── */}
          {activeTab === 'members' && (
            <div className="space-y-4">
              {/* Member list */}
              <div className="card">
                <h3 className="font-semibold text-gray-800 mb-3 text-sm">Group Members</h3>
                <div className="space-y-2">
                  {family.members?.map(m => (
                    <div key={m.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                      <div className="w-9 h-9 bg-teal-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                        {m.name[0]}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-700 text-sm">{m.name}</p>
                        <p className="text-xs text-gray-400">{m.email}</p>
                      </div>
                      {m.is_owner && <span className="badge-green text-xs">Owner</span>}
                      {family.is_owner && !m.is_owner && (
                        <button
                          onClick={() => removeMember(m.id, m.name)}
                          className="text-gray-400 hover:text-red-500 transition-colors"
                          title="Remove member"
                        >
                          <UserMinus size={15} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Invite form (owner only) */}
              {family.is_owner && (
                <div className="card">
                  <h3 className="font-semibold text-gray-800 mb-3 text-sm flex items-center gap-2">
                    <UserPlus size={15} className="text-teal-500" /> Invite a Member
                  </h3>
                  <form onSubmit={handleInvite} className="flex gap-2">
                    <input
                      className="input flex-1 text-sm"
                      type="email"
                      placeholder="email@example.com"
                      value={inviteEmail}
                      onChange={e => setInviteEmail(e.target.value)}
                    />
                    <button type="submit" disabled={inviting} className="btn-primary px-4 text-sm">
                      {inviting ? '…' : 'Send Invite'}
                    </button>
                  </form>
                  <p className="text-xs text-gray-400 mt-2">
                    The user must have a FinAdvisor AI account. They will see a notification to accept.
                  </p>
                </div>
              )}

              {/* Pending invitations (owner only) */}
              {family.is_owner && (family.pending_invitations?.length ?? 0) > 0 && (
                <div className="card">
                  <h3 className="font-semibold text-gray-800 mb-3 text-sm flex items-center gap-2">
                    <Clock size={15} className="text-orange-500" /> Pending Invitations
                  </h3>
                  <div className="space-y-2">
                    {family.pending_invitations?.map(inv => (
                      <div key={inv.id} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg text-sm">
                        <span className="font-medium text-gray-700">{inv.invited_email}</span>
                        <span className="text-xs text-orange-500 font-medium">Pending</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Transactions tab ── */}
          {activeTab === 'transactions' && (
            <FamilyTransactionsList month={month} year={year} />
          )}
        </>
      )}
    </div>
  )
}

// ─── Family Transactions List ─────────────────────────────────────────────────

function FamilyTransactionsList({ month, year }: { month: number; year: number }) {
  const [transactions, setTransactions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.get('/family/transactions', { params: { month, year } })
      .then(res => setTransactions(res.data.transactions || []))
      .catch(() => toast.error('Failed to load transactions'))
      .finally(() => setLoading(false))
  }, [month, year])

  if (loading) return (
    <div className="flex justify-center py-10">
      <div className="w-6 h-6 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (transactions.length === 0) return (
    <div className="card flex flex-col items-center justify-center py-10 gap-3">
      <DollarSign size={24} className="text-gray-300" />
      <p className="text-sm text-gray-500">No transactions found for this period.</p>
    </div>
  )

  return (
    <div className="card">
      <h3 className="font-semibold text-gray-800 mb-3 text-sm">All Member Transactions</h3>
      <div className="space-y-2">
        {transactions.map((t: any) => (
          <div key={t.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg text-sm">
            <div>
              <p className="font-medium text-gray-700">{t.description}</p>
              <p className="text-xs text-gray-400">{t.category} · {t.member_name} · {t.date}</p>
            </div>
            <span className={`font-semibold ${t.type === 'income' ? 'text-green-600' : 'text-red-500'}`}>
              {t.type === 'income' ? '+' : '-'}{formatCurrency(t.amount)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
