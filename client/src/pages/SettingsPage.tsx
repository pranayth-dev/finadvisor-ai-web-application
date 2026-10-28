import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import api from '../services/api'
import { Settings as SettingsIcon, Bell, Moon, Sun, User, DollarSign } from 'lucide-react'
import toast from 'react-hot-toast'
import type { Notification } from '../types'
import { formatDate } from '../utils/formatters'

export default function SettingsPage() {
  const { user, updateUser } = useAuth()
  const [settings, setSettings] = useState({
    theme: user?.theme || 'light',
    account_mode: user?.account_mode || 'individual',
    currency: user?.currency || 'INR',
    notification_budget_alerts: user?.notification_budget_alerts ?? true,
    notification_goal_milestones: user?.notification_goal_milestones ?? true,
    notification_monthly_summary: user?.notification_monthly_summary ?? true,
  })
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unread, setUnread] = useState(0)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.get('/notifications')
      .then(res => {
        setNotifications(res.data.notifications)
        setUnread(res.data.unread_count)
      })
      .catch(() => {})
  }, [])

  async function saveSettings() {
    setSaving(true)
    try {
      const res = await api.put('/profile', settings)
      updateUser(res.data.user)
      if (settings.theme === 'dark') document.documentElement.classList.add('dark')
      else document.documentElement.classList.remove('dark')
      toast.success('Settings saved')
    } catch { toast.error('Failed to save settings') }
    finally { setSaving(false) }
  }

  async function markAllRead() {
    try {
      await api.put('/notifications/read-all')
      setNotifications(ns => ns.map(n => ({ ...n, is_read: true })))
      setUnread(0)
      toast.success('All notifications marked as read')
    } catch { toast.error('Failed') }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <SettingsIcon size={20} className="text-teal-500" /> Settings
        </h1>
        <p className="text-sm text-gray-500">Manage your preferences</p>
      </div>

      {/* Appearance */}
      <div className="card">
        <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          {settings.theme === 'dark' ? <Moon size={16} className="text-teal-500" /> : <Sun size={16} className="text-teal-500" />}
          Appearance
        </h2>
        <div className="flex gap-3">
          <button
            onClick={() => setSettings(s => ({ ...s, theme: 'light' }))}
            className={`flex-1 py-3 rounded-xl border-2 transition-colors text-sm font-medium ${
              settings.theme === 'light' ? 'border-teal-400 bg-teal-50 text-teal-700' : 'border-gray-200 text-gray-500'
            }`}
          >
            ☀️ Light Mode
          </button>
          <button
            onClick={() => setSettings(s => ({ ...s, theme: 'dark' }))}
            className={`flex-1 py-3 rounded-xl border-2 transition-colors text-sm font-medium ${
              settings.theme === 'dark' ? 'border-teal-400 bg-teal-50 text-teal-700' : 'border-gray-200 text-gray-500'
            }`}
          >
            🌙 Dark Mode
          </button>
        </div>
      </div>

      {/* Account Mode */}
      <div className="card">
        <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <User size={16} className="text-teal-500" /> Account Mode
        </h2>
        <div className="flex gap-3">
          {(['individual', 'family'] as const).map(mode => (
            <button key={mode}
              onClick={() => setSettings(s => ({ ...s, account_mode: mode }))}
              className={`flex-1 py-3 rounded-xl border-2 transition-colors text-sm font-medium capitalize ${
                settings.account_mode === mode ? 'border-teal-400 bg-teal-50 text-teal-700' : 'border-gray-200 text-gray-500'
              }`}
            >
              {mode === 'individual' ? '👤' : '👨‍👩‍👧'} {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-2">Family mode enables shared finance tracking with family members.</p>
      </div>

      {/* Notifications */}
      <div className="card">
        <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <Bell size={16} className="text-teal-500" /> Notification Preferences
        </h2>
        <div className="space-y-3">
          {[
            { key: 'notification_budget_alerts', label: 'Budget Alerts', desc: 'Alert when budget reaches 80% or over limit' },
            { key: 'notification_goal_milestones', label: 'Goal Milestones', desc: 'Celebrate savings goal progress' },
            { key: 'notification_monthly_summary', label: 'Monthly Summary', desc: 'Monthly financial overview' },
          ].map(({ key, label, desc }) => (
            <label key={key} className="flex items-center justify-between cursor-pointer">
              <div>
                <p className="text-sm font-medium text-gray-700">{label}</p>
                <p className="text-xs text-gray-400">{desc}</p>
              </div>
              <div className="relative">
                <input type="checkbox"
                  checked={settings[key as keyof typeof settings] as boolean}
                  onChange={e => setSettings(s => ({ ...s, [key]: e.target.checked }))}
                  className="sr-only" />
                <div
                  onClick={() => setSettings(s => ({ ...s, [key]: !s[key as keyof typeof s] }))}
                  className={`w-11 h-6 rounded-full cursor-pointer transition-colors ${
                    settings[key as keyof typeof settings] ? 'bg-teal-500' : 'bg-gray-200'
                  }`}
                >
                  <div className={`w-4 h-4 bg-white rounded-full mt-1 transition-transform ${
                    settings[key as keyof typeof settings] ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      <button onClick={saveSettings} disabled={saving} className="btn-primary flex items-center gap-2">
        {saving ? 'Saving…' : 'Save All Settings'}
      </button>

      {/* Notifications Center */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-800 flex items-center gap-2">
            <Bell size={16} className="text-teal-500" /> Notification Center
            {unread > 0 && (
              <span className="bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full">{unread}</span>
            )}
          </h2>
          {unread > 0 && (
            <button onClick={markAllRead} className="text-xs text-teal-600 hover:underline">
              Mark all read
            </button>
          )}
        </div>
        {notifications.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-6">No notifications</p>
        ) : (
          <div className="space-y-2">
            {notifications.map(n => (
              <div key={n.id} className={`p-3 rounded-lg border ${n.is_read ? 'bg-gray-50 border-gray-100' : 'bg-blue-50 border-blue-200'}`}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className={`text-sm font-medium ${n.is_read ? 'text-gray-600' : 'text-gray-800'}`}>{n.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{n.message}</p>
                    <p className="text-xs text-gray-400 mt-1">{formatDate(n.created_at)}</p>
                  </div>
                  {!n.is_read && <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 shrink-0" />}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
