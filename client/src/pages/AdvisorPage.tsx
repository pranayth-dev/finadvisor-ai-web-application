import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Brain, RefreshCw, CheckCircle, AlertTriangle, AlertCircle,
  Info, TrendingUp, Target, PieChart, Send, Bot, User, Globe, Lock,
  Wallet, Receipt, BarChart2, CreditCard, Lightbulb, HelpCircle,
  Percent, ShoppingBag, CalendarClock, Star, RotateCcw,
  BookOpen, PiggyBank, Scale, TrendingDown, DollarSign, ShieldCheck,
  Eye, Trash2, X, ExternalLink,
} from 'lucide-react'
import api from '../services/api'
import type { FinancialInsight, HealthScore, SavedChatMessage } from '../types'
import { formatDate, getPriorityColor } from '../utils/formatters'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  source?: string
  timestamp: Date
}

interface QuestionDef {
  label: string
  icon: React.ElementType
  color: string   // Tailwind bg class for the icon circle
}

// ---------------------------------------------------------------------------
// Predefined question banks
// ---------------------------------------------------------------------------

const PERSONAL_QUESTIONS: QuestionDef[] = [
  { label: 'How much money can I save this month?',     icon: PiggyBank,     color: 'bg-teal-100 text-teal-700' },
  { label: 'What bills are coming up?',                 icon: CalendarClock, color: 'bg-orange-100 text-orange-700' },
  { label: 'Analyze my spending habits.',               icon: BarChart2,     color: 'bg-blue-100 text-blue-700' },
  { label: 'Am I on track with my savings goals?',      icon: Target,        color: 'bg-purple-100 text-purple-700' },
  { label: 'How can I reduce my monthly expenses?',     icon: TrendingDown,  color: 'bg-red-100 text-red-700' },
  { label: 'Give me a summary of my monthly finances.', icon: Receipt,       color: 'bg-green-100 text-green-700' },
  { label: 'Which spending category costs me the most?',icon: ShoppingBag,   color: 'bg-yellow-100 text-yellow-700' },
  { label: 'How much of my income am I spending?',      icon: Percent,       color: 'bg-indigo-100 text-indigo-700' },
  { label: 'Can I afford a planned purchase?',          icon: CreditCard,    color: 'bg-pink-100 text-pink-700' },
  { label: 'Create a personalised budget for me.',      icon: Wallet,        color: 'bg-teal-100 text-teal-700' },
]

const GENERAL_QUESTIONS: QuestionDef[] = [
  { label: 'How do I create a monthly budget?',                    icon: Wallet,      color: 'bg-teal-100 text-teal-700' },
  { label: 'What is the 50/30/20 budgeting rule?',                 icon: Scale,       color: 'bg-blue-100 text-blue-700' },
  { label: 'What is compound interest?',                           icon: TrendingUp,  color: 'bg-green-100 text-green-700' },
  { label: 'How do I build an emergency fund?',                    icon: ShieldCheck, color: 'bg-orange-100 text-orange-700' },
  { label: 'What are the best ways to save money?',                icon: PiggyBank,   color: 'bg-purple-100 text-purple-700' },
  { label: 'What is the difference between saving and investing?', icon: DollarSign,  color: 'bg-indigo-100 text-indigo-700' },
  { label: 'How can beginners manage their debt?',                 icon: CreditCard,  color: 'bg-red-100 text-red-700' },
  { label: 'What is inflation and how does it affect money?',      icon: BarChart2,   color: 'bg-yellow-100 text-yellow-700' },
  { label: 'How can I improve my financial discipline?',           icon: Star,        color: 'bg-pink-100 text-pink-700' },
  { label: 'What financial goals should I set for the future?',    icon: Target,      color: 'bg-teal-100 text-teal-700' },
]

// ---------------------------------------------------------------------------
// Greeting messages
// ---------------------------------------------------------------------------

const GREETINGS: Record<'general' | 'personal', string> = {
  general: "Hello! I'm FinAdvisor AI — your personal finance education assistant.\n\nClick any question below or type your own. No account needed.",
  personal: "Hello! I'm your personal FinAdvisor AI.\n\nClick a question below to get an instant answer based on your real financial data, or type your own.",
}

// ---------------------------------------------------------------------------
// Markdown renderer (bold, bullets)
// ---------------------------------------------------------------------------

function RenderContent({ content }: { content: string }) {
  return (
    <div className="space-y-0.5">
      {content.split('\n').map((line, j) => {
        // Bullet lines
        if (line.startsWith('• ') || line.startsWith('- ')) {
          const text = line.slice(2)
          return (
            <div key={j} className="flex gap-1.5">
              <span className="mt-1.5 w-1 h-1 rounded-full bg-current shrink-0 opacity-60" />
              <span>{renderBold(text)}</span>
            </div>
          )
        }
        return (
          <p key={j} className={j > 0 ? 'mt-0.5' : ''}>
            {renderBold(line)}
          </p>
        )
      })}
    </div>
  )
}

function renderBold(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/)
  return (
    <>
      {parts.map((part, k) =>
        part.startsWith('**') && part.endsWith('**')
          ? <strong key={k}>{part.slice(2, -2)}</strong>
          : <span key={k}>{part}</span>
      )}
    </>
  )
}

// ---------------------------------------------------------------------------
// Question card grid
// ---------------------------------------------------------------------------

function QuestionGrid({
  questions,
  onSelect,
  disabled,
}: {
  questions: QuestionDef[]
  onSelect: (label: string) => void
  disabled: boolean
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
      {questions.map((q) => {
        const Icon = q.icon
        return (
          <button
            key={q.label}
            onClick={() => onSelect(q.label)}
            disabled={disabled}
            className={`
              flex items-start gap-3 p-3 rounded-xl border text-left
              transition-all duration-150 group
              bg-white dark:bg-gray-800
              border-gray-100 dark:border-gray-700
              hover:border-teal-300 hover:shadow-sm hover:bg-teal-50/50 dark:hover:bg-gray-700
              focus:outline-none focus:ring-2 focus:ring-teal-400 focus:ring-offset-1
              disabled:opacity-40 disabled:cursor-not-allowed
            `}
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${q.color}`}>
              <Icon size={15} />
            </div>
            <span className="text-sm text-gray-700 dark:text-gray-200 leading-snug group-hover:text-teal-700 dark:group-hover:text-teal-300">
              {q.label}
            </span>
          </button>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Chat panel
// ---------------------------------------------------------------------------

function ChatPanel({
  mode,
  endpoint,
  questions,
  subtitle,
}: {
  mode: 'general' | 'personal'
  endpoint: string
  questions: QuestionDef[]
  subtitle: string
}) {
  // Stable greeting — recreated only when mode actually changes
  const greetingRef = useRef<ChatMessage>({
    role: 'assistant',
    content: GREETINGS[mode],
    timestamp: new Date(),
  })

  const [messages, setMessages] = useState<ChatMessage[]>([greetingRef.current])
  const [input, setInput] = useState('')
  // `loading` is tracked via a ref AND state: the ref prevents a second in-flight
  // request even if the setter hasn't flushed yet (important in Strict Mode).
  const loadingRef = useRef(false)
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [showCards, setShowCards] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)
  // AbortController so an in-flight history load is cancelled when we start a new chat
  const historyAbortRef = useRef<AbortController | null>(null)

  function setLoadingBoth(val: boolean) {
    loadingRef.current = val
    setLoading(val)
  }

  // Reset + optionally reload history when mode changes
  useEffect(() => {
    // Cancel any in-progress history fetch from the previous mode
    historyAbortRef.current?.abort()

    const g: ChatMessage = { role: 'assistant', content: GREETINGS[mode], timestamp: new Date() }
    greetingRef.current = g
    setMessages([g])
    setInput('')
    setConversationId(null)
    setShowCards(true)
    loadingRef.current = false
    setLoading(false)

    loadLastConversation(g)
  // mode is the only real dependency — the function is defined inside and uses it
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function loadLastConversation(greeting: ChatMessage) {
    // General tab: skip history pre-load (no auth requirement)
    if (mode === 'general') return

    const controller = new AbortController()
    historyAbortRef.current = controller

    try {
      const res = await api.get('/advisor/conversations', {
        params: { advisor_type: mode, limit: 1 },
        signal: controller.signal,
      })
      if (controller.signal.aborted) return
      const convs = res.data.conversations
      if (!convs?.length) return

      const latest = convs[0]
      const msgRes = await api.get('/advisor/messages', {
        params: { advisor_type: mode, conversation_id: latest.conversation_id },
        signal: controller.signal,
      })
      if (controller.signal.aborted) return

      const saved: SavedChatMessage[] = msgRes.data.messages
      if (!saved?.length) return

      // Deduplicate: keep only unique (role, content) pairs in insertion order
      const seen = new Set<string>()
      const loaded: ChatMessage[] = []
      for (const m of saved) {
        const key = `${m.role}::${m.content}`
        if (!seen.has(key)) {
          seen.add(key)
          loaded.push({
            role: m.role,
            content: m.content,
            source: m.ai_provider ? providerLabel(m.ai_provider) : undefined,
            timestamp: new Date(m.created_at),
          })
        }
      }
      if (!loaded.length) return

      setConversationId(latest.conversation_id)
      setMessages([greeting, ...loaded])
      setShowCards(false)
    } catch (err: any) {
      if (err?.name === 'CanceledError' || err?.name === 'AbortError') return
      // Non-critical — silently ignore other errors
    }
  }

  function providerLabel(source: string) {
    const map: Record<string, string> = {
      gemini: 'Google Gemini 1.5 Flash',
      openai: 'OpenAI GPT-4o-mini',
      builtin: 'FinAdvisor Built-in Engine',
    }
    return map[source] ?? source
  }

  function startNewChat() {
    historyAbortRef.current?.abort()
    const g: ChatMessage = { role: 'assistant', content: GREETINGS[mode], timestamp: new Date() }
    greetingRef.current = g
    setMessages([g])
    setInput('')
    setConversationId(null)
    setShowCards(true)
    loadingRef.current = false
    setLoading(false)
  }

  // ── send ──────────────────────────────────────────────────────────────────
  // Called by question-card clicks and form submit.
  // IMPORTANT: fireRequest is called OUTSIDE setState so React Strict Mode's
  // double-invocation of updater functions does not fire it twice.
  async function send(text: string) {
    const q = text.trim()
    // Guard: reject empty text or any already-in-flight request
    if (!q || loadingRef.current) return

    setInput('')
    setShowCards(false)
    setLoadingBoth(true)

    const newMsg: ChatMessage = { role: 'user', content: q, timestamp: new Date() }

    // Capture current messages synchronously, then append the user message.
    // We do NOT call fireRequest from inside the state setter — that was the
    // root cause of the duplicate: Strict Mode calls updaters twice.
    setMessages(prev => [...prev, newMsg])

    // Build history from current displayed messages + the new user message.
    // We read messages directly here; the setState above is async but we have
    // the correct snapshot via closure.
    await fireRequest(q, conversationId)
  }

  async function fireRequest(question: string, convId: string | null) {
    // Re-read current messages from a ref so we always send the correct history
    // regardless of render timing.
    // We send the question directly rather than re-deriving it from state to
    // avoid any async-state-race issues.
    try {
      const payload: Record<string, unknown> = {
        question,
      }
      if (convId) payload.conversation_id = convId

      const res = await api.post(endpoint, payload)

      if (res.data.conversation_id) {
        setConversationId(res.data.conversation_id)
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.data.answer,
        source: res.data.ai_provider,
        timestamp: new Date(),
      }])
    } catch (err: any) {
      const errMsg = err.response?.data?.error || 'Unable to connect. Please try again.'
      toast.error('AI request failed')
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `⚠️ ${errMsg}`,
        timestamp: new Date(),
      }])
    } finally {
      setLoadingBoth(false)
    }
  }

  const hasConversation = messages.length > 1

  return (
    <div className="space-y-4">
      {/* Question card grid — always shown until user starts chatting */}
      <div className="card dark:bg-gray-800 dark:border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold text-gray-800 dark:text-white">
              {mode === 'personal' ? 'Personal Finance Questions' : 'Financial Education Topics'}
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">Click any question for an instant answer</p>
          </div>
          {hasConversation && (
            <button
              onClick={startNewChat}
              className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-teal-600 dark:text-gray-400 dark:hover:text-teal-400 transition-colors"
            >
              <RotateCcw size={13} />
              New Chat
            </button>
          )}
        </div>
        <QuestionGrid questions={questions} onSelect={send} disabled={loading} />
      </div>

      {/* Chat area — shown once there is at least one exchange */}
      {hasConversation && (
        <div className="card flex flex-col dark:bg-gray-800 dark:border-gray-700" style={{ minHeight: '340px', maxHeight: '540px' }}>
          {/* Header */}
          <div className="flex items-center gap-2 pb-2.5 border-b dark:border-gray-700 mb-3 shrink-0">
            <Brain size={15} className="text-teal-500" />
            <h3 className="font-semibold text-gray-800 dark:text-white text-sm">
              {mode === 'general' ? 'Finance Education Chat' : 'My Personal Finance Chat'}
            </h3>
            <span className="text-xs text-gray-400 ml-auto">{subtitle}</span>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-3 pr-1 min-h-0">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 bg-teal-100 dark:bg-teal-900 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                    <Bot size={13} className="text-teal-600 dark:text-teal-400" />
                  </div>
                )}
                <div className={`max-w-[82%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-teal-500 text-white'
                    : 'bg-gray-50 dark:bg-gray-700 text-gray-800 dark:text-gray-100 border border-gray-100 dark:border-gray-600'
                }`}>
                  <RenderContent content={msg.content} />
                  {msg.source && (
                    <p className={`text-xs mt-1.5 ${msg.role === 'user' ? 'text-teal-200' : 'text-gray-400'}`}>
                      via {msg.source}
                    </p>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-7 h-7 bg-teal-500 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                    <User size={13} className="text-white" />
                  </div>
                )}
              </div>
            ))}

            {/* Typing indicator */}
            {loading && (
              <div className="flex gap-2 justify-start">
                <div className="w-7 h-7 bg-teal-100 dark:bg-teal-900 rounded-full flex items-center justify-center shrink-0">
                  <Bot size={13} className="text-teal-600" />
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 border border-gray-100 dark:border-gray-600 rounded-xl px-4 py-3">
                  <span className="flex gap-1 items-center">
                    <span className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Free-text input */}
          <form
            onSubmit={e => { e.preventDefault(); send(input) }}
            className="flex gap-2 pt-3 border-t dark:border-gray-700 mt-2 shrink-0"
          >
            <input
              className="input flex-1 text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              placeholder={mode === 'general'
                ? 'Ask anything about personal finance…'
                : 'Ask about your income, expenses, goals…'}
              value={input}
              onChange={e => setInput(e.target.value)}
              disabled={loading}
              maxLength={1000}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="btn-primary px-4 flex items-center gap-1 disabled:opacity-50"
            >
              <Send size={15} />
            </button>
          </form>
        </div>
      )}

      {/* Empty state — only when no conversation started yet */}
      {!hasConversation && (
        <div className="card flex flex-col items-center justify-center py-8 text-center dark:bg-gray-800 dark:border-gray-700">
          <Bot size={32} className="text-teal-400 mb-3" />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Click any question above to start, or type your own question.
          </p>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Insight detail modal
// ---------------------------------------------------------------------------

function InsightDetailModal({
  insight,
  onClose,
}: {
  insight: FinancialInsight
  onClose: () => void
}) {
  const navigate = useNavigate()
  const icons: Record<string, React.ElementType> = {
    spending: TrendingUp, savings: CheckCircle, budget: PieChart,
    goal: Target, info: Info,
  }
  const Icon = icons[insight.insight_type] || Info
  const colorClass = getPriorityColor(insight.priority)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`flex items-start gap-3 p-5 border-b dark:border-gray-700 ${colorClass} rounded-t-2xl`}>
          <Icon size={20} className="mt-0.5 shrink-0" />
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-base leading-snug">{insight.title}</h3>
            <span className={`inline-block text-xs px-2 py-0.5 rounded-full font-medium capitalize mt-1 border ${colorClass}`}>
              {insight.priority} priority · {insight.insight_type}
            </span>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-full hover:bg-black/10 transition-colors shrink-0"
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4">
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Summary</h4>
            <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-line">
              {insight.message}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            {insight.category && (
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                <p className="text-gray-400 mb-0.5">Category</p>
                <p className="font-semibold text-gray-800 dark:text-gray-100">{insight.category}</p>
              </div>
            )}
            {insight.month && insight.year && (
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                <p className="text-gray-400 mb-0.5">Period</p>
                <p className="font-semibold text-gray-800 dark:text-gray-100">
                  {new Date(insight.year, (insight.month ?? 1) - 1).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}
                </p>
              </div>
            )}
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <p className="text-gray-400 mb-0.5">Type</p>
              <p className="font-semibold text-gray-800 dark:text-gray-100 capitalize">{insight.insight_type}</p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <p className="text-gray-400 mb-0.5">Generated</p>
              <p className="font-semibold text-gray-800 dark:text-gray-100">{formatDate(insight.created_at)}</p>
            </div>
          </div>

          {insight.action_label && insight.action_url && (
            <button
              onClick={() => { navigate(insight.action_url!); onClose() }}
              className="flex items-center gap-2 w-full justify-center px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-semibold hover:bg-teal-700 transition-colors"
            >
              <ExternalLink size={14} />
              {insight.action_label}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Insight card
// ---------------------------------------------------------------------------

function InsightCard({
  insight,
  onDeleted,
}: {
  insight: FinancialInsight
  onDeleted: (id: number) => void
}) {
  const colorClass = getPriorityColor(insight.priority)
  const navigate = useNavigate()
  const [showDetail, setShowDetail] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const icons: Record<string, React.ElementType> = {
    spending: TrendingUp, savings: CheckCircle, budget: PieChart,
    goal: Target, info: Info,
  }
  const Icon = icons[insight.insight_type] || Info

  async function handleDelete() {
    setDeleting(true)
    try {
      await api.delete(`/advisor/insights/${insight.id}`)
      toast.success('Insight dismissed')
      onDeleted(insight.id)
    } catch {
      toast.error('Failed to delete insight')
    } finally {
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  return (
    <>
      {showDetail && <InsightDetailModal insight={insight} onClose={() => setShowDetail(false)} />}

      <div className={`rounded-xl border p-4 ${colorClass}`}>
        <div className="flex items-start gap-3">
          <Icon size={18} className="mt-0.5 shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2 flex-wrap mb-1">
              <h4 className="font-semibold text-sm">{insight.title}</h4>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize border ${colorClass}`}>
                {insight.priority}
              </span>
            </div>
            <p className="text-sm opacity-90 leading-relaxed">{insight.message}</p>
            {insight.action_label && insight.action_url && (
              <button
                onClick={() => navigate(insight.action_url!)}
                className="mt-2 text-xs font-semibold underline opacity-80 hover:opacity-100"
              >
                {insight.action_label} →
              </button>
            )}
            <p className="text-xs opacity-50 mt-2">{formatDate(insight.created_at)}</p>

            {/* Action buttons */}
            <div className="flex items-center gap-2 mt-3 pt-2 border-t border-current/10">
              <button
                onClick={() => setShowDetail(true)}
                className="flex items-center gap-1.5 text-xs font-medium opacity-70 hover:opacity-100 transition-opacity"
              >
                <Eye size={12} /> Show Details
              </button>

              {!confirmDelete ? (
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="flex items-center gap-1.5 text-xs font-medium opacity-70 hover:opacity-100 transition-opacity ml-auto"
                >
                  <Trash2 size={12} /> Dismiss
                </button>
              ) : (
                <div className="flex items-center gap-1.5 ml-auto">
                  <span className="text-xs opacity-70">Delete this insight?</span>
                  <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="text-xs font-semibold text-red-600 hover:text-red-700 disabled:opacity-50"
                  >
                    {deleting ? '…' : 'Yes'}
                  </button>
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className="text-xs font-semibold opacity-60 hover:opacity-100"
                  >
                    No
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

// ---------------------------------------------------------------------------
// Health score card
// ---------------------------------------------------------------------------

function HealthScoreCard({ score }: { score: HealthScore | null }) {
  if (!score) return null
  const color = score.score >= 80 ? 'text-green-600'
    : score.score >= 60 ? 'text-teal-600'
    : score.score >= 40 ? 'text-yellow-600'
    : 'text-red-600'
  const bg = score.score >= 80 ? 'bg-green-50 border-green-200'
    : score.score >= 60 ? 'bg-teal-50 border-teal-200'
    : score.score >= 40 ? 'bg-yellow-50 border-yellow-200'
    : 'bg-red-50 border-red-200'

  return (
    <div className={`card border ${bg}`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-bold text-gray-800">Financial Health Score</h3>
          <p className="text-sm text-gray-500">Based on your real financial data</p>
        </div>
        <div className="text-center">
          <p className={`text-4xl font-black ${color}`}>{score.score}</p>
          <p className={`text-sm font-semibold ${color}`}>{score.grade}</p>
          <p className="text-xs text-gray-400">out of 100</p>
        </div>
      </div>
      <div className="space-y-2 mb-4">
        {score.breakdown.map(b => (
          <div key={b.factor}>
            <div className="flex justify-between text-xs mb-0.5 text-gray-500">
              <span>{b.factor}</span>
              <span className="font-medium">{b.score}/{b.max}</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-teal-500 transition-all"
                style={{ width: `${(b.score / b.max) * 100}%` }}
              />
            </div>
            <p className="text-xs text-gray-400 mt-0.5">{b.note}</p>
          </div>
        ))}
      </div>
      {score.strengths.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-semibold text-green-700 mb-1">✓ Strengths</p>
          <div className="flex flex-wrap gap-1">
            {score.strengths.map(s => <span key={s} className="badge-green">{s}</span>)}
          </div>
        </div>
      )}
      {score.areas_for_improvement.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-orange-700 mb-1">⚡ Areas to Improve</p>
          <div className="flex flex-wrap gap-1">
            {score.areas_for_improvement.map(s => <span key={s} className="badge-yellow">{s}</span>)}
          </div>
        </div>
      )}
      <p className="text-xs text-gray-400 mt-3 border-t pt-2">
        ℹ️ This score is informational and not a certified financial or credit score.
      </p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

type Tab = 'general' | 'personal' | 'insights' | 'health'

export default function AdvisorPage() {
  const [insights, setInsights] = useState<FinancialInsight[]>([])
  const [healthScore, setHealthScore] = useState<HealthScore | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [activeTab, setActiveTab] = useState<Tab>('general')

  const loadInsights = useCallback(async () => {
    try {
      const [insightsRes, healthRes] = await Promise.all([
        api.get('/advisor/insights'),
        api.get('/advisor/health-score'),
      ])
      setInsights(insightsRes.data.insights)
      setHealthScore(healthRes.data)
    } catch {
      toast.error('Failed to load advisor data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadInsights() }, [loadInsights])

  async function runAnalysis() {
    setAnalyzing(true)
    try {
      const res = await api.post('/advisor/analyze')
      const count = res.data.count
      if (count === 0) {
        toast.success('Insights are up to date — no new items this month')
      } else {
        toast.success(`Generated ${count} new insight${count !== 1 ? 's' : ''}`)
      }
      await loadInsights()
    } catch {
      toast.error('Analysis failed')
    } finally {
      setAnalyzing(false)
    }
  }

  function handleInsightDeleted(id: number) {
    setInsights(prev => prev.filter(i => i.id !== id))
  }

  const critical = insights.filter(i => i.priority === 'critical')
  const high = insights.filter(i => i.priority === 'high')
  const others = insights.filter(i => !['critical', 'high'].includes(i.priority))

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'general',  label: 'Finance Chat',               icon: Globe },
    { id: 'personal', label: 'My Finances',                icon: Lock },
    { id: 'insights', label: `Insights (${insights.length})`, icon: Brain },
    { id: 'health',   label: 'Health Score',               icon: CheckCircle },
  ]

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
            <Brain size={22} className="text-teal-500" /> AI Financial Advisor
          </h1>
          <p className="text-sm text-gray-500">
            General finance education · Personalised insights · Health score
          </p>
        </div>
        {(activeTab === 'insights' || activeTab === 'health') && (
          <button
            onClick={runAnalysis}
            disabled={analyzing}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw size={16} className={analyzing ? 'animate-spin' : ''} />
            {analyzing ? 'Analyzing…' : 'Run Analysis'}
          </button>
        )}
      </div>

      {/* Disclaimer */}
      <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-xl p-3 text-sm text-blue-700 dark:text-blue-300 flex items-start gap-2">
        <Info size={15} className="mt-0.5 shrink-0" />
        <span>
          FinAdvisor AI provides <strong>educational information</strong> and data-driven summaries.
          It is not a certified financial advisor. For major financial decisions, consult a qualified professional.
        </span>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg flex-wrap">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === id
                ? 'bg-white dark:bg-gray-700 shadow-sm text-teal-600 dark:text-teal-400'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            }`}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}

      {activeTab === 'general' && (
        <div className="space-y-4">
          <div className="bg-teal-50 dark:bg-teal-950 border border-teal-100 dark:border-teal-800 rounded-xl p-3 text-sm text-teal-800 dark:text-teal-300 flex items-start gap-2">
            <Globe size={15} className="mt-0.5 shrink-0" />
            <span>
              <strong>No account needed.</strong> Click a question or type your own.
              Answers come from a real AI model, not hardcoded rules.
            </span>
          </div>
          <ChatPanel
            mode="general"
            endpoint="/advisor/general-chat"
            questions={GENERAL_QUESTIONS}
            subtitle="No login required · General financial education"
          />
        </div>
      )}

      {activeTab === 'personal' && (
        <div className="space-y-4">
          <div className="bg-green-50 dark:bg-green-950 border border-green-100 dark:border-green-800 rounded-xl p-3 text-sm text-green-800 dark:text-green-300 flex items-start gap-2">
            <Lock size={15} className="mt-0.5 shrink-0" />
            <span>
              <strong>Your real data.</strong> Answers use your actual transactions, budgets,
              savings goals, and bills. Your data stays on your account.
            </span>
          </div>
          <ChatPanel
            mode="personal"
            endpoint="/advisor/chat"
            questions={PERSONAL_QUESTIONS}
            subtitle="Uses your real financial data"
          />
        </div>
      )}

      {activeTab === 'insights' && (
        loading ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : insights.length === 0 ? (
          <div className="card flex flex-col items-center justify-center py-16 gap-4">
            <div className="w-16 h-16 bg-teal-50 rounded-full flex items-center justify-center">
              <Brain size={28} className="text-teal-400" />
            </div>
            <div className="text-center">
              <p className="font-medium text-gray-700 mb-1">No insights yet</p>
              <p className="text-sm text-gray-400 mb-4">
                Run analysis to generate personalised financial insights.
              </p>
            </div>
            <button onClick={runAnalysis} disabled={analyzing} className="btn-primary flex items-center gap-2">
              <Brain size={16} /> Run Analysis
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {critical.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-red-600 mb-2 flex items-center gap-1">
                  <AlertCircle size={14} /> Critical ({critical.length})
                </h3>
                <div className="space-y-3">{critical.map(i => <InsightCard key={i.id} insight={i} onDeleted={handleInsightDeleted} />)}</div>
              </div>
            )}
            {high.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-orange-600 mb-2 flex items-center gap-1">
                  <AlertTriangle size={14} /> High Priority ({high.length})
                </h3>
                <div className="space-y-3">{high.map(i => <InsightCard key={i.id} insight={i} onDeleted={handleInsightDeleted} />)}</div>
              </div>
            )}
            {others.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-600 mb-2">Other Insights ({others.length})</h3>
                <div className="space-y-3">{others.map(i => <InsightCard key={i.id} insight={i} onDeleted={handleInsightDeleted} />)}</div>
              </div>
            )}
          </div>
        )
      )}

      {activeTab === 'health' && (
        loading ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <HealthScoreCard score={healthScore} />
        )
      )}
    </div>
  )
}
