import { useState, useEffect } from 'react'
import { Menu, Bell, Sun, Moon } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

interface TopBarProps { onMenuClick: () => void }

export default function TopBar({ onMenuClick }: TopBarProps) {
  const { user, updateUser } = useAuth()
  const navigate = useNavigate()
  const [unread, setUnread] = useState(0)

  useEffect(() => {
    api.get('/notifications').then(res => setUnread(res.data.unread_count)).catch(() => {})
  }, [])

  function toggleTheme() {
    const newTheme = user?.theme === 'dark' ? 'light' : 'dark'
    if (newTheme === 'dark') document.documentElement.classList.add('dark')
    else document.documentElement.classList.remove('dark')
    api.put('/profile', { theme: newTheme })
      .then(res => updateUser(res.data.user))
      .catch(() => {})
  }

  const today = new Date().toLocaleDateString('en-IN', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  })

  return (
    <header className="h-14 bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700 flex items-center px-4 gap-3 shrink-0">
      <button onClick={onMenuClick} className="lg:hidden text-gray-500 hover:text-teal-600">
        <Menu size={22} />
      </button>

      <div className="flex-1 hidden sm:block">
        <p className="text-xs text-gray-400 dark:text-gray-500">{today}</p>
      </div>

      <div className="flex items-center gap-2 ml-auto">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          {user?.theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* Notifications */}
        <button
          onClick={() => navigate('/settings')}
          className="relative w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <Bell size={18} />
          {unread > 0 && (
            <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center font-bold">
              {unread > 9 ? '9+' : unread}
            </span>
          )}
        </button>

        {/* Avatar */}
        <div className="w-8 h-8 bg-teal-500 rounded-full flex items-center justify-center text-white text-xs font-bold cursor-pointer"
          onClick={() => navigate('/profile')}>
          {user?.first_name?.[0]}{user?.last_name?.[0]}
        </div>
      </div>
    </header>
  )
}
