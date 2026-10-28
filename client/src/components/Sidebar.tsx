import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, ArrowLeftRight, PieChart, Target,
  Brain, FileText, Users, Settings, User, X, TrendingUp, Bell
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/transactions', label: 'Transactions', icon: ArrowLeftRight },
  { to: '/budgets', label: 'Budgets', icon: PieChart },
  { to: '/goals', label: 'Savings Goals', icon: Target },
  { to: '/bills', label: 'Bills', icon: Bell },
  { to: '/advisor', label: 'AI Advisor', icon: Brain },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/family', label: 'Family Finance', icon: Users },
]

const bottomItems = [
  { to: '/profile', label: 'Profile', icon: User },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export default function Sidebar({ open, onClose }: SidebarProps) {
  const { user, logout } = useAuth()

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-30 w-64 bg-teal-700 text-white flex flex-col
        transform transition-transform duration-300 ease-in-out
        ${open ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}
    >
      {/* Logo */}
      <div className="flex items-center justify-between px-5 py-5 border-b border-teal-600">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white/10 rounded-lg flex items-center justify-center">
            <TrendingUp size={20} className="text-teal-200" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white">FinAdvisor AI</h1>
            <p className="text-xs text-teal-300">Smart Money. Better Decisions.</p>
          </div>
        </div>
        <button onClick={onClose} className="lg:hidden text-teal-300 hover:text-white">
          <X size={20} />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="px-3 mb-2 text-xs font-semibold uppercase tracking-wider text-teal-400">
          Main Menu
        </p>
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
              ${isActive
                ? 'bg-white/15 text-white'
                : 'text-teal-200 hover:bg-white/10 hover:text-white'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Bottom items */}
      <div className="px-3 pb-4 border-t border-teal-600 pt-3 space-y-0.5">
        <p className="px-3 mb-2 text-xs font-semibold uppercase tracking-wider text-teal-400">
          Account
        </p>
        {bottomItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
              ${isActive
                ? 'bg-white/15 text-white'
                : 'text-teal-200 hover:bg-white/10 hover:text-white'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
        {/* User card */}
        <div className="mt-3 px-3 py-3 bg-white/10 rounded-lg">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-teal-500 rounded-full flex items-center justify-center text-sm font-bold text-white">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-white truncate">{user?.full_name}</p>
              <p className="text-xs text-teal-300 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full mt-2 text-xs text-teal-300 hover:text-white transition-colors text-left"
          >
            Sign out →
          </button>
        </div>
      </div>
    </aside>
  )
}
