import { Link } from 'react-router-dom'
import {
  TrendingUp, BarChart2, Target, Brain, Shield, Users,
  PiggyBank, CreditCard, Bell, ChevronRight, CheckCircle,
  Zap, Lock, Globe, ArrowRight, Star,
} from 'lucide-react'

const FEATURES = [
  {
    icon: BarChart2,
    color: 'bg-teal-100 text-teal-700',
    title: 'Financial Dashboard',
    desc: 'Get a real-time overview of your income, expenses, net savings, and spending patterns — all in one place.',
  },
  {
    icon: CreditCard,
    color: 'bg-blue-100 text-blue-700',
    title: 'Transaction & Income Tracking',
    desc: 'Record every rupee in and out. Categorize transactions, add notes, and search your financial history with ease.',
  },
  {
    icon: Target,
    color: 'bg-purple-100 text-purple-700',
    title: 'Budget Management',
    desc: 'Set monthly category budgets and track utilization. Get alerts when spending approaches or exceeds your limits.',
  },
  {
    icon: PiggyBank,
    color: 'bg-green-100 text-green-700',
    title: 'Savings Goals',
    desc: 'Define goals like emergency fund or vacation, set target amounts and dates, and track your progress month by month.',
  },
  {
    icon: Bell,
    color: 'bg-orange-100 text-orange-700',
    title: 'Bills & Reminders',
    desc: 'Never miss a payment. Track recurring bills, see upcoming due dates, and manage all your subscriptions.',
  },
  {
    icon: Brain,
    color: 'bg-pink-100 text-pink-700',
    title: 'AI Personal Finance Advisor',
    desc: 'Ask questions about your real financial data. Get personalized answers based on your transactions, budgets, and goals.',
  },
  {
    icon: Globe,
    color: 'bg-indigo-100 text-indigo-700',
    title: 'General Finance Education',
    desc: 'Learn budgeting rules, compound interest, debt management, and more — no login required.',
  },
  {
    icon: Zap,
    color: 'bg-yellow-100 text-yellow-700',
    title: 'Financial Insights & Health Score',
    desc: 'Automated analysis detects spending spikes, budget overruns, and savings opportunities. Your health score summarizes your position.',
  },
  {
    icon: Users,
    color: 'bg-teal-100 text-teal-700',
    title: 'Family Finance',
    desc: 'Create a shared family group, track combined income and expenses, and manage shared savings goals together.',
  },
  {
    icon: BarChart2,
    color: 'bg-red-100 text-red-700',
    title: 'Reports & Analytics',
    desc: 'Generate monthly financial reports with income/expense breakdowns, trends, and a narrative summary of your finances.',
  },
]

const HOW_IT_WORKS = [
  {
    step: '01',
    title: 'Create an Account',
    desc: 'Register in seconds. Your financial data is private and accessible only to you.',
  },
  {
    step: '02',
    title: 'Enter Income & Transactions',
    desc: 'Record your salary, freelance income, and every expense. Categorize them for better analysis.',
  },
  {
    step: '03',
    title: 'Set Budgets & Savings Goals',
    desc: 'Define monthly spending limits per category and create goals for what matters to you.',
  },
  {
    step: '04',
    title: 'Review Financial Insights',
    desc: 'Run analysis to get personalized insights about your spending patterns and financial health.',
  },
  {
    step: '05',
    title: 'Ask the AI Advisor',
    desc: 'Chat with your personal AI advisor about your actual financial data for guidance tailored to you.',
  },
]

const BENEFITS = [
  'Understand exactly where your money goes each month',
  'Identify overspending before it becomes a problem',
  'Build healthy saving habits with goal tracking',
  'Monitor multiple budgets simultaneously',
  'Receive AI-generated insights from your real data',
  'Plan for the future with projections and savings targets',
  'Manage household finances collaboratively with family',
  'Make informed financial decisions with data, not guesswork',
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white font-sans text-gray-800">
      {/* ── Navigation ── */}
      <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-gray-100 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-teal-600 rounded-lg flex items-center justify-center">
              <TrendingUp size={18} className="text-white" />
            </div>
            <div>
              <span className="font-bold text-gray-900 text-base leading-tight block">FinAdvisor AI</span>
              <span className="text-teal-600 text-xs leading-tight block">Smart Money. Better Decisions.</span>
            </div>
          </div>

          {/* Desktop links */}
          <div className="hidden md:flex items-center gap-6 text-sm text-gray-600">
            <a href="#features" className="hover:text-teal-600 transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-teal-600 transition-colors">How It Works</a>
            <a href="#benefits" className="hover:text-teal-600 transition-colors">Benefits</a>
            <a href="#security" className="hover:text-teal-600 transition-colors">Security</a>
          </div>

          {/* Auth buttons */}
          <div className="flex items-center gap-2">
            <Link
              to="/login"
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-teal-600 transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="px-4 py-2 text-sm font-semibold bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="bg-gradient-to-br from-teal-700 via-teal-600 to-teal-800 text-white py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-white/15 border border-white/20 text-teal-100 text-xs font-medium px-3 py-1.5 rounded-full mb-6">
            <Star size={12} /> AI-Powered Personal Finance
          </div>
          <h1 className="text-4xl sm:text-5xl font-black mb-5 leading-tight">
            Smart Money.<br />Better Decisions.
          </h1>
          <p className="text-teal-100 text-lg sm:text-xl max-w-2xl mx-auto mb-8 leading-relaxed">
            FinAdvisor AI helps you track spending, manage budgets, plan savings, and understand
            your financial habits — powered by a real AI advisor that uses <em>your</em> actual data.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/register"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-teal-700 font-bold rounded-xl hover:bg-teal-50 transition-colors text-base shadow-lg"
            >
              Get Started Free <ArrowRight size={17} />
            </Link>
            <a
              href="#features"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white/15 border border-white/30 text-white font-semibold rounded-xl hover:bg-white/25 transition-colors text-base"
            >
              Explore Features
            </a>
          </div>

          {/* Mini stats */}
          <div className="mt-14 grid grid-cols-3 gap-6 max-w-lg mx-auto">
            {[
              { value: '10+', label: 'Feature Areas' },
              { value: 'AI', label: 'Powered Advisor' },
              { value: '100%', label: 'Private Data' },
            ].map(({ value, label }) => (
              <div key={label} className="text-center">
                <p className="text-3xl font-black text-white">{value}</p>
                <p className="text-teal-200 text-xs mt-0.5">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" className="py-20 px-4 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-black text-gray-900 mb-3">Everything You Need</h2>
            <p className="text-gray-500 max-w-xl mx-auto">
              One application covering the full picture of your personal finances —
              from daily transactions to long-term goals.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map(({ icon: Icon, color, title, desc }) => (
              <div
                key={title}
                className="bg-white rounded-2xl p-6 border border-gray-100 hover:shadow-md transition-shadow"
              >
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-4 ${color}`}>
                  <Icon size={20} />
                </div>
                <h3 className="font-bold text-gray-900 mb-1.5">{title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section id="how-it-works" className="py-20 px-4 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-black text-gray-900 mb-3">How It Works</h2>
            <p className="text-gray-500">Get from zero to financial clarity in five steps.</p>
          </div>
          <div className="space-y-6">
            {HOW_IT_WORKS.map(({ step, title, desc }, i) => (
              <div key={step} className="flex gap-5 items-start">
                <div className="w-12 h-12 bg-teal-600 text-white rounded-xl flex items-center justify-center font-black text-sm shrink-0">
                  {step}
                </div>
                <div className="pt-1">
                  <h3 className="font-bold text-gray-900 mb-1">{title}</h3>
                  <p className="text-gray-500 text-sm leading-relaxed">{desc}</p>
                </div>
                {i < HOW_IT_WORKS.length - 1 && (
                  <ChevronRight size={18} className="text-gray-300 shrink-0 mt-3 hidden sm:block" />
                )}
              </div>
            ))}
          </div>
          <div className="mt-10 text-center">
            <Link
              to="/register"
              className="inline-flex items-center gap-2 px-6 py-3 bg-teal-600 text-white font-bold rounded-xl hover:bg-teal-700 transition-colors"
            >
              Start Your Journey <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Benefits ── */}
      <section id="benefits" className="py-20 px-4 bg-teal-700 text-white">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-black mb-3">Why FinAdvisor AI?</h2>
            <p className="text-teal-200 max-w-xl mx-auto">
              Real financial clarity comes from understanding your habits, not just checking your balance.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {BENEFITS.map(benefit => (
              <div key={benefit} className="flex items-start gap-3 bg-white/10 border border-white/15 rounded-xl p-4">
                <CheckCircle size={18} className="text-teal-300 shrink-0 mt-0.5" />
                <span className="text-teal-50 text-sm leading-relaxed">{benefit}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Security ── */}
      <section id="security" className="py-20 px-4 bg-white">
        <div className="max-w-3xl mx-auto text-center">
          <div className="w-14 h-14 bg-teal-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <Shield size={26} className="text-teal-600" />
          </div>
          <h2 className="text-3xl font-black text-gray-900 mb-4">Your Data Stays Private</h2>
          <p className="text-gray-500 text-base leading-relaxed max-w-xl mx-auto mb-8">
            Every financial record you enter belongs exclusively to you. FinAdvisor AI uses
            JWT-based authentication to ensure that only you can access your own transactions,
            budgets, goals, bills, and insights.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 text-left">
            {[
              {
                icon: Lock,
                title: 'Authenticated Access',
                desc: 'Your account is protected by secure passwords and signed tokens. Unauthenticated requests cannot access any personal data.',
              },
              {
                icon: Shield,
                title: 'User-Scoped Records',
                desc: 'Every API call verifies ownership. You can only view or modify records that belong to your account.',
              },
              {
                icon: CheckCircle,
                title: 'No Shared Exposure',
                desc: 'Your financial data is never shown to other users. Family groups share only what you explicitly agree to share together.',
              },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="bg-gray-50 border border-gray-100 rounded-xl p-5">
                <div className="w-9 h-9 bg-teal-100 rounded-lg flex items-center justify-center mb-3">
                  <Icon size={17} className="text-teal-600" />
                </div>
                <h3 className="font-bold text-gray-900 mb-1 text-sm">{title}</h3>
                <p className="text-gray-500 text-xs leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
          <p className="mt-6 text-xs text-gray-400">
            FinAdvisor AI provides educational financial information and data-driven summaries.
            It is not a licensed financial advisor. For major financial decisions, consult a qualified professional.
          </p>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-16 px-4 bg-gray-50 border-t border-gray-100">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl font-black text-gray-900 mb-3">Ready to take control of your finances?</h2>
          <p className="text-gray-500 mb-7">Free to start. No credit card required.</p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/register"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-teal-600 text-white font-bold rounded-xl hover:bg-teal-700 transition-colors"
            >
              Create Free Account <ArrowRight size={16} />
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-gray-200 text-gray-700 font-semibold rounded-xl hover:border-teal-300 hover:text-teal-700 transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="bg-gray-900 text-gray-400 py-12 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-8 mb-10">
            {/* Brand */}
            <div className="sm:col-span-2">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center">
                  <TrendingUp size={15} className="text-white" />
                </div>
                <span className="text-white font-bold text-sm">FinAdvisor AI</span>
              </div>
              <p className="text-xs leading-relaxed max-w-xs">
                Smart Money. Better Decisions. A personal finance management application
                with AI-powered insights to help you understand and improve your financial health.
              </p>
            </div>

            {/* Navigation */}
            <div>
              <h4 className="text-white text-sm font-semibold mb-3">Navigation</h4>
              <ul className="space-y-2 text-xs">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a></li>
                <li><a href="#benefits" className="hover:text-white transition-colors">Benefits</a></li>
                <li><a href="#security" className="hover:text-white transition-colors">Security</a></li>
              </ul>
            </div>

            {/* Account */}
            <div>
              <h4 className="text-white text-sm font-semibold mb-3">Account</h4>
              <ul className="space-y-2 text-xs">
                <li><Link to="/login" className="hover:text-white transition-colors">Sign In</Link></li>
                <li><Link to="/register" className="hover:text-white transition-colors">Register</Link></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-gray-800 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
            <p>© {new Date().getFullYear()} FinAdvisor AI. All rights reserved.</p>
            <p className="text-gray-600">
              This application provides educational financial information only. Not certified financial advice.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
