import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import api from '../services/api'
import { User as UserIcon, Mail, Phone, Lock, Trash2, Save } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ProfilePage() {
  const { user, updateUser, logout } = useAuth()
  const [form, setForm] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.phone || '',
    monthly_income_preference: user?.monthly_income_preference?.toString() || '0',
  })
  const [saving, setSaving] = useState(false)
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm: '' })
  const [pwSaving, setPwSaving] = useState(false)
  const [pwErrors, setPwErrors] = useState<Record<string, string>>({})
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deletePassword, setDeletePassword] = useState('')

  async function handleProfileSave(e: React.FormEvent) {
    e.preventDefault()
    if (!form.first_name.trim() || !form.last_name.trim()) {
      toast.error('Name fields are required')
      return
    }
    setSaving(true)
    try {
      const res = await api.put('/profile', {
        ...form,
        monthly_income_preference: Number(form.monthly_income_preference) || 0,
      })
      updateUser(res.data.user)
      toast.success('Profile updated')
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to update profile')
    } finally { setSaving(false) }
  }

  async function handlePasswordChange(e: React.FormEvent) {
    e.preventDefault()
    const errs: Record<string, string> = {}
    if (!pwForm.current_password) errs.current_password = 'Current password is required'
    if (pwForm.new_password.length < 8) errs.new_password = 'New password must be at least 8 characters'
    if (pwForm.new_password !== pwForm.confirm) errs.confirm = 'Passwords do not match'
    setPwErrors(errs)
    if (Object.keys(errs).length) return
    setPwSaving(true)
    try {
      await api.post('/auth/change-password', {
        current_password: pwForm.current_password,
        new_password: pwForm.new_password,
      })
      toast.success('Password changed')
      setPwForm({ current_password: '', new_password: '', confirm: '' })
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to change password')
    } finally { setPwSaving(false) }
  }

  async function handleDeleteAccount() {
    try {
      await api.delete('/profile/delete', { data: { password: deletePassword } })
      toast.success('Account deactivated')
      logout()
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to delete account')
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-800">Profile</h1>
        <p className="text-sm text-gray-500">Manage your personal information</p>
      </div>

      {/* Avatar */}
      <div className="card flex items-center gap-4">
        <div className="w-16 h-16 bg-teal-500 rounded-full flex items-center justify-center text-white text-xl font-bold">
          {user?.first_name?.[0]}{user?.last_name?.[0]}
        </div>
        <div>
          <p className="font-bold text-gray-800 text-lg">{user?.full_name}</p>
          <p className="text-sm text-gray-500 flex items-center gap-1"><Mail size={13} /> {user?.email}</p>
          <p className="text-xs text-gray-400 mt-1">Member since {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' }) : ''}</p>
        </div>
      </div>

      {/* Edit profile form */}
      <div className="card">
        <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <UserIcon size={16} className="text-teal-500" /> Personal Information
        </h2>
        <form onSubmit={handleProfileSave} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">First Name</label>
              <input className="input" value={form.first_name}
                onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))} />
            </div>
            <div>
              <label className="label">Last Name</label>
              <input className="input" value={form.last_name}
                onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))} />
            </div>
          </div>
          <div>
            <label className="label">Phone Number</label>
            <input type="tel" className="input" value={form.phone}
              onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
          </div>
          <div>
            <label className="label">Monthly Income Preference (₹)</label>
            <input type="number" min="0" className="input" value={form.monthly_income_preference}
              onChange={e => setForm(f => ({ ...f, monthly_income_preference: e.target.value }))} />
            <p className="text-xs text-gray-400 mt-1">Your expected monthly income for planning purposes</p>
          </div>
          <button type="submit" disabled={saving}
            className="btn-primary flex items-center gap-2">
            <Save size={15} /> {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </form>
      </div>

      {/* Change Password */}
      <div className="card">
        <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <Lock size={16} className="text-teal-500" /> Change Password
        </h2>
        <form onSubmit={handlePasswordChange} className="space-y-3">
          <div>
            <label className="label">Current Password</label>
            <input type="password" className="input" value={pwForm.current_password}
              onChange={e => setPwForm(f => ({ ...f, current_password: e.target.value }))} />
            {pwErrors.current_password && <p className="text-red-500 text-xs mt-1">{pwErrors.current_password}</p>}
          </div>
          <div>
            <label className="label">New Password</label>
            <input type="password" className="input" value={pwForm.new_password}
              onChange={e => setPwForm(f => ({ ...f, new_password: e.target.value }))} />
            {pwErrors.new_password && <p className="text-red-500 text-xs mt-1">{pwErrors.new_password}</p>}
          </div>
          <div>
            <label className="label">Confirm New Password</label>
            <input type="password" className="input" value={pwForm.confirm}
              onChange={e => setPwForm(f => ({ ...f, confirm: e.target.value }))} />
            {pwErrors.confirm && <p className="text-red-500 text-xs mt-1">{pwErrors.confirm}</p>}
          </div>
          <button type="submit" disabled={pwSaving} className="btn-primary flex items-center gap-2">
            <Lock size={15} /> {pwSaving ? 'Changing…' : 'Change Password'}
          </button>
        </form>
      </div>

      {/* Delete Account */}
      <div className="card border-red-200">
        <h2 className="font-semibold text-red-700 mb-3 flex items-center gap-2">
          <Trash2 size={16} /> Danger Zone
        </h2>
        <p className="text-sm text-gray-500 mb-3">
          Deactivating your account will disable access. Your data will be retained for recovery.
        </p>
        {!showDeleteConfirm ? (
          <button onClick={() => setShowDeleteConfirm(true)} className="btn-danger text-sm py-1.5 px-4">
            Deactivate Account
          </button>
        ) : (
          <div className="space-y-3 border border-red-200 p-4 rounded-lg bg-red-50">
            <p className="text-sm text-red-700 font-medium">Confirm deactivation — enter your password:</p>
            <input type="password" className="input" placeholder="Your password"
              value={deletePassword} onChange={e => setDeletePassword(e.target.value)} />
            <div className="flex gap-2">
              <button onClick={handleDeleteAccount} className="btn-danger flex-1">Confirm Deactivate</button>
              <button onClick={() => { setShowDeleteConfirm(false); setDeletePassword('') }}
                className="btn-secondary flex-1">Cancel</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
