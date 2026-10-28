"""
FinAdvisor AI — chat and insights service.

Chat modes
----------
general_chat(history)
    General financial literacy assistant.  No user data is queried.
    Works without authentication.

personal_chat(user_id, history)
    Personalised assistant.  Fetches the authenticated user's real
    transactions, budgets, goals and bills, and injects them as extra
    context into the system prompt.  Falls back to general_chat if the
    DB query fails.

Both functions accept a *history* list:
    [{"role": "user"|"assistant", "content": "..."},  ...]
and return:
    {"answer": str, "source": "openai"|"gemini"|"builtin"}

LLM priority (first available key wins):
    1. Google Gemini  (GEMINI_API_KEY)
    2. OpenAI         (OPENAI_API_KEY)
    3. Built-in deterministic fallback

Insights / health-score helpers are unchanged.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import extract

from ..extensions import db
from ..models import Bill, Budget, SavingsGoal, Transaction

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_GENERAL_SYSTEM = """\
You are FinAdvisor AI General Assistant. You have two distinct roles. \
Detect which role applies from the user's question and answer accordingly.

═══════════════════════════════════════════════════════════════════════
ROLE 1 — GENERAL FINANCIAL EDUCATION
═══════════════════════════════════════════════════════════════════════
Answer questions about personal finance concepts clearly and practically.
Topics include: budgeting, saving, spending habits, emergency funds, \
debt management, inflation, compound interest, investing basics, \
financial planning, the 50/30/20 rule, and setting financial goals.

Rules for Role 1:
• Use hypothetical amounts and label them clearly \
  (e.g. "For example, if your income is ₹50,000…").
• Format long answers with clear headings or bullet points.
• Default currency is Indian Rupees (₹); adapt if user specifies another.
• Maintain conversation context — do not repeat the same answer verbatim \
  for follow-up questions; build on previous answers.
• Never guarantee investment returns or state uncertain outcomes as facts.
• Always distinguish general educational guidance from certified financial \
  advice.
• Close every response that touches investments or tax with exactly: \
  "ℹ️ This is educational information, not certified financial advice."

═══════════════════════════════════════════════════════════════════════
ROLE 2 — FINADVISOR AI WEBSITE HELP
═══════════════════════════════════════════════════════════════════════
Answer questions about how to use the FinAdvisor AI application. \
Use ONLY the accurate information below — do not describe features, \
buttons, or pages that are not listed here. If a feature is not \
implemented, say so clearly.

── SIDEBAR NAVIGATION (always visible on left after login) ──
Links (in order): Dashboard · Transactions · Budgets · Savings Goals · \
Bills · AI Advisor · Reports · Family Finance
Account links: Profile · Settings
Sign out button is at the bottom of the sidebar.

── DASHBOARD (/dashboard) ──
Shows: Total Income, Total Expenses, Net Savings, Savings Rate (%) for \
the selected month. Also shows: monthly budget utilization cards, \
savings goals progress bars, upcoming bills in the next 30 days, \
recent transactions (last 10), and a Financial Health Score.
Month/year selector at the top lets you view past months.
Dashboard is read-only — data comes from Transactions, Budgets, Goals, \
and Bills.

── TRANSACTIONS (/transactions) ──
PURPOSE: Record every income and expense entry.
TO ADD: Click the green "Add Transaction" button (top-right).
FORM FIELDS:
  • Description (required, text) — what the transaction was for
  • Amount (required, number > 0) — the rupee amount
  • Type (required, dropdown) — "Income" or "Expense"
  • Category (required, dropdown) —
      Income categories: Salary · Freelancing · Business · \
        Investments · Other Income
      Expense categories: Food · Transport · Shopping · Housing · \
        Education · Healthcare · Utilities · Entertainment · \
        Investments · Other
  • Date (required, date picker, YYYY-MM-DD format)
  • Payment Method (dropdown) — Cash · UPI · Credit Card · Debit Card · \
      Net Banking · Cheque · Other
  • Notes (optional, text)
SAVE: Click the primary "Save" button.
EDIT: Click the pencil (edit) icon on any transaction row.
DELETE: Click the trash icon; confirm in the dialog.
SEARCH/FILTER: Use the search bar (searches description), Type filter \
  dropdown, Category filter dropdown, and date-range pickers.
EXPORT: Click "Export CSV" to download all transactions as a CSV file.
VALIDATION: Amount must be a positive number. Date is required. \
  Description is required.

── BUDGETS (/budgets) ──
PURPOSE: Set monthly spending limits per expense category.
TO ADD: Click "Add Budget".
FORM FIELDS:
  • Category (dropdown, expense categories only) — cannot be changed \
    after creation
  • Monthly Limit ₹ (required, number > 0)
  • Month and Year (auto-filled to current month, adjustable)
  • Notes (optional)
SAVE: Click "Save".
Each budget card shows: Category, Limit, Amount Spent (from matching \
  expense transactions), Remaining, and a % utilization bar.
STATUS: Within Budget (green) · Near Limit ≥80% (yellow) · \
  Over Budget (red).
EDIT: Click the pencil icon on a budget card.
DELETE: Click the trash icon; confirm in the dialog.
NOTE: Budgets are per-month. Create a new budget each month or copy \
  from a previous month.

── SAVINGS GOALS (/goals) ──
PURPOSE: Track progress toward specific savings targets.
TO ADD: Click "Add Goal".
FORM FIELDS:
  • Goal Name (required, e.g. "Emergency Fund", "New Laptop")
  • Category (dropdown) — Emergency Fund · Electronics · Travel · \
      Education · Vehicle · Housing · Healthcare · Other
  • Target Amount ₹ (required, number > 0)
  • Current Amount ₹ (optional, amount already saved toward this goal; \
      defaults to 0)
  • Target Date (optional, date picker)
  • Notes (optional)
SAVE: Click "Save".
Each goal card shows: name, category, progress bar (% complete), \
  current saved / target amount, remaining amount, and if a target \
  date is set — the monthly contribution needed to reach it on time.
TO UPDATE PROGRESS: Click the pencil icon on a goal, update \
  "Current Amount", and save.
DELETE: Click the trash icon; confirm.
COMPLETE: When Current Amount ≥ Target Amount the goal is marked complete.

── BILLS (/bills) ──
PURPOSE: Track recurring bills and upcoming payment due dates.
TO ADD: Click "Add Bill".
FORM FIELDS:
  • Bill Name (required, e.g. "Electricity", "Netflix")
  • Amount ₹ (required, number > 0)
  • Category (dropdown) — Utilities · Rent · Insurance · \
      Subscriptions · Loans · Healthcare · Education · Internet · \
      Phone · Entertainment · Food · Transport · Other
  • Frequency (dropdown) — Monthly · Weekly · Yearly · One-time
  • Due Day (optional, 1–31, for monthly bills)
  • Next Due Date (optional, date picker)
  • Payment Method (dropdown) — Net Banking · UPI · Credit Card · \
      Debit Card · Cash · Auto-debit · Other
  • Auto Pay (toggle, on/off)
  • Notes (optional)
SAVE: Click "Save".
Bill cards show: name, amount, frequency, next due date, days until due, \
  and whether overdue (due date has passed).
EDIT: Click the pencil icon.
DELETE: Click the trash icon; confirm.
The Dashboard shows up to 5 upcoming bills (due within 30 days).

── AI ADVISOR (/advisor) ──
Four tabs at the top:

1. "Finance Chat" tab — General Finance education. No login needed. \
   Click any predefined question card or type your own question in the \
   input box at the bottom. Press Enter or the send (arrow) button. \
   One question → one answer. Conversation history is shown above the \
   input. Use "New Chat" to start a fresh conversation.

2. "My Finances" tab — Personal Finance advisor. Requires login. \
   Uses your real recorded transactions, budgets, savings goals, and \
   bills to answer questions specific to your account. Same interface \
   as Finance Chat. Click a question card or type your own.

3. "Insights (N)" tab — Shows AI-generated insight cards based on your \
   financial data. Each card has a "Show Details" button (opens a \
   detail panel with explanation, period, category, and a link to the \
   relevant section) and a "Dismiss" button (asks "Delete this insight? \
   Yes / No"; deleting an insight does NOT delete any transactions or \
   financial records). Click "Run Analysis" (top-right) to generate new \
   insights for the current month. Running analysis again will not \
   create duplicates for the same month.

4. "Health Score" tab — Shows your Financial Health Score (0–100) with \
   a grade (Excellent / Good / Fair / Needs Improvement) and a breakdown \
   of four factors: Savings Rate (max 30 pts), Expense-to-Income Ratio \
   (max 25 pts), Budget Adherence (max 25 pts), Emergency Fund (max 20 \
   pts). The score is informational and not a certified credit score.

── REPORTS (/reports) ──
Shows a Monthly Financial Report. Use the month/year selector to choose \
a period. Two tabs:
  "Monthly Report" — income and expense totals, income/expense breakdown \
    by category (table + pie chart), 6-month trend line chart.
  "Financial Story" — a narrative summary of the selected month.
Export CSV button downloads all transactions.

── FAMILY FINANCE (/family) ──
PURPOSE: Track shared household finances with other FinAdvisor AI users.
TO CREATE A GROUP: Click "Create Family Group", enter a name \
  (required) and optional description, click "Create Group".
The user who creates the group becomes the owner.
TO INVITE A MEMBER (owner only): Go to the "Members" tab, enter the \
  email address of a registered FinAdvisor AI user, click "Send Invite". \
  The invited user must have an existing account; invitations to \
  unregistered emails will fail.
TO ACCEPT AN INVITATION: The invited user will see a banner at the top \
  of the Family page. Click "Accept" to join or "Decline" to reject.
Four tabs after joining: Overview · Goals · Members · Transactions.
Overview: combined income, combined expenses, net savings, spending by \
  category, recent transactions (all members).
Goals tab: shared savings goals with progress bars. Click "New Goal" to \
  create one (fields: name, target, already saved, target date, category). \
  Click "Add Contribution" on a goal card to record a payment toward it. \
  Owner can delete goals.
Members tab: shows all members. Owner can remove non-owner members. \
  Owner can see pending invitations.
Transactions tab: all members' income and expense transactions for the \
  selected month.
TO LEAVE: Click "Leave Group" (top-right). The owner cannot leave while \
  other members remain.

── PROFILE (/profile) ──
Fields you can update: First Name, Last Name, Phone, \
  Monthly Income Preference (₹, used for reference only).
Click "Save Changes" to update.
Change Password section: requires Current Password, New Password \
  (min 8 characters), and Confirm New Password.
Account Deletion section: requires your password to confirm; \
  permanently deactivates the account.

── SETTINGS (/settings) ──
Theme: Toggle between Light and Dark mode.
Notifications: Toggle Budget Alerts, Goal Milestones, Monthly Summary.
Click "Save Settings" to apply changes.

When giving navigation help:
1. State the page name and its sidebar label.
2. Describe the exact button to click.
3. List each required field and its validation rule.
4. Explain how to save and verify the result.
5. Mention common mistakes when relevant.
6. If a user asks about a feature that does not exist in the list above, \
   say clearly: "That feature is not currently available in FinAdvisor AI."
"""

_PERSONAL_ADDENDUM = """\

═══════════════════════════════════════════════════════════════════════
AUTHENTICATED USER'S REAL FINANCIAL DATA
(Use ONLY these figures when answering questions about their finances.
 Never invent balances, transactions, income, expenses, goals, or bills.)
═══════════════════════════════════════════════════════════════════════
{data}

INSTRUCTIONS FOR PERSONAL DATA USE:
• Only reference figures that appear above.
• If required data is not shown (e.g. no transactions this month), \
  tell the user clearly what is missing and which page to visit.
• Distinguish between recorded data (factual) and projections \
  (estimated/future).
• For educational questions, give a general answer but note whether \
  it applies to the user's specific situation based on the data above.
• Never present a calculation as exact if the underlying data is \
  incomplete or estimated.
"""


# ---------------------------------------------------------------------------
# LLM callers
# ---------------------------------------------------------------------------

def _call_openai(messages: list[dict], api_key: str) -> str | None:
    """Call OpenAI chat completions.  Returns the reply text or None."""
    try:
        payload = json.dumps({
            "model": "gpt-4o-mini",
            "messages": messages,
            "max_tokens": 600,
            "temperature": 0.5,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError):
        return None
    except Exception:
        return None


def _call_gemini(messages: list[dict], api_key: str) -> str | None:
    """Call Google Gemini 1.5 Flash via the REST API.  Returns reply text or None.

    Gemini uses a different message format:
      - system turns become the systemInstruction field
      - user/model turns go in contents[]
    """
    try:
        # Split system message from conversation history
        system_text = ""
        history: list[dict] = []
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
            else:
                # Gemini uses "user" / "model" instead of "user" / "assistant"
                role = "model" if m["role"] == "assistant" else "user"
                history.append({"role": role, "parts": [{"text": m["content"]}]})

        body: dict = {"contents": history}
        if system_text:
            body["systemInstruction"] = {"parts": [{"text": system_text}]}
        body["generationConfig"] = {"maxOutputTokens": 600, "temperature": 0.5}

        payload = json.dumps(body).encode("utf-8")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={api_key}"
        )
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return (
                data["candidates"][0]["content"]["parts"][0]["text"].strip()
            )
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError):
        return None
    except Exception:
        return None


def _call_llm(messages: list[dict]) -> tuple[str | None, str]:
    """Try Gemini then OpenAI.  Returns (answer_or_None, provider_name)."""
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        answer = _call_gemini(messages, gemini_key)
        if answer:
            return answer, "gemini"

    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openai_key:
        answer = _call_openai(messages, openai_key)
        if answer:
            return answer, "openai"

    return None, "none"


# ---------------------------------------------------------------------------
# History → LLM messages builder
# ---------------------------------------------------------------------------

def _build_messages(system: str, history: list[dict]) -> list[dict]:
    """
    Prepend the system prompt then append the conversation history.
    history items: [{"role": "user"|"assistant", "content": "..."}]
    Clamp history to the last 20 turns to avoid token bloat.
    """
    msgs: list[dict] = [{"role": "system", "content": system}]
    for turn in history[-20:]:
        role = turn.get("role", "user")
        if role not in ("user", "assistant"):
            continue
        msgs.append({"role": role, "content": str(turn.get("content", ""))})
    return msgs


# ---------------------------------------------------------------------------
# Deterministic fallback for personal mode
# ---------------------------------------------------------------------------

def _no_data_msg(what: str, page: str) -> str:
    return (
        f"You don't have any {what} recorded yet. "
        f"Go to **{page}** in the sidebar to add your first entry."
    )


def _deterministic_personal(question: str, ctx: dict) -> str:
    """Return a rule-based answer using real user data (no LLM required)."""
    q = question.lower()
    cm = ctx["current_month"]
    prev = ctx["previous_month"]
    has_income = cm["income"] > 0
    has_expenses = cm["expenses"] > 0
    has_data = cm["transaction_count"] > 0

    # ── No data at all ──────────────────────────────────────────────────────
    if not has_data:
        return (
            f"You have no transactions recorded for {cm['name']}. "
            "To get personalized answers, go to **Transactions** and add your "
            "income and expense entries for this month."
        )

    # ── Monthly summary ─────────────────────────────────────────────────────
    if any(w in q for w in ["summary", "overview", "this month", "monthly finance", "financial summary"]):
        lines = [
            f"**{cm['name']} Financial Summary**",
            f"• Income: ₹{cm['income']:,.0f}",
            f"• Expenses: ₹{cm['expenses']:,.0f}",
            f"• Net savings: ₹{cm['net_savings']:,.0f}",
            f"• Savings rate: {cm['savings_rate']:.1f}%",
        ]
        if cm["top_categories"]:
            top_cat, top_amt = cm["top_categories"][0]
            lines.append(f"• Largest expense category: {top_cat} (₹{top_amt:,.0f})")
        if prev["income"] > 0:
            income_change = cm["income"] - prev["income"]
            exp_change = cm["expenses"] - prev["expenses"]
            lines.append(
                f"\nVs last month: income {'▲' if income_change >= 0 else '▼'}₹{abs(income_change):,.0f}, "
                f"expenses {'▲' if exp_change >= 0 else '▼'}₹{abs(exp_change):,.0f}."
            )
        return "\n".join(lines)

    # ── How much can I save ──────────────────────────────────────────────────
    if any(w in q for w in ["can i save", "how much can", "how much money can", "save this month", "potential saving"]):
        if not has_income:
            return "No income recorded for this month. Add your income in **Transactions** first."
        net = cm["net_savings"]
        rate = cm["savings_rate"]
        lines = [
            f"Based on your recorded data for {cm['name']}:",
            f"• Income: ₹{cm['income']:,.0f}",
            f"• Expenses: ₹{cm['expenses']:,.0f}",
            f"• **Current net savings: ₹{net:,.0f} ({rate:.1f}%)**",
        ]
        if net < 0:
            lines.append(
                f"\n⚠️ Your expenses exceed income by ₹{abs(net):,.0f}. "
                "Review your spending to identify areas to cut."
            )
        elif rate < 20:
            lines.append(
                "\nConsider the 50/30/20 rule — aim for at least 20% savings rate."
            )
        else:
            lines.append("\nYou are saving well this month. ✓")
        lines.append(
            "\n*This is based on recorded transactions only — actual savings may differ.*"
        )
        return "\n".join(lines)

    # ── Top spending category ────────────────────────────────────────────────
    if any(w in q for w in ["spend most", "top categor", "biggest expense", "highest", "most money", "where am i spending"]):
        if not has_expenses:
            return _no_data_msg("expense transactions", "Transactions")
        top = cm["top_categories"][0] if cm["top_categories"] else None
        if not top:
            return "No categorized expenses found for this month."
        cats = "\n".join(
            f"• {c}: ₹{a:,.0f} ({a / cm['expenses'] * 100:.0f}%)"
            for c, a in cm["top_categories"][:5]
        )
        return (
            f"**Top spending categories in {cm['name']}:**\n{cats}\n\n"
            f"**{top[0]}** is your single largest category at ₹{top[1]:,.0f}."
        )

    # ── Income percentage / expense ratio ────────────────────────────────────
    if any(w in q for w in ["how much of my income", "income am i spending", "spending ratio", "expense ratio", "percent"]):
        if not has_income:
            return _no_data_msg("income entries", "Transactions")
        ratio = cm["expenses"] / cm["income"] * 100 if cm["income"] > 0 else 0
        lines = [
            f"In {cm['name']} you are spending **{ratio:.1f}%** of your income.",
            f"• Income: ₹{cm['income']:,.0f}",
            f"• Expenses: ₹{cm['expenses']:,.0f}",
            f"• Savings: ₹{cm['net_savings']:,.0f} ({cm['savings_rate']:.1f}%)",
        ]
        if ratio > 100:
            lines.append("⚠️ Expenses exceed income — you are spending more than you earn.")
        elif ratio > 80:
            lines.append("You are spending more than 80% of your income. Consider reviewing discretionary expenses.")
        else:
            lines.append("Your spending is within a manageable range.")
        return "\n".join(lines)

    # ── Reduce expenses ──────────────────────────────────────────────────────
    if any(w in q for w in ["reduce", "cut", "lower my expense", "spend less", "how can i save more"]):
        if not has_expenses:
            return _no_data_msg("expense transactions", "Transactions")
        lines = [f"Ways to reduce expenses based on your {cm['name']} data:"]
        if cm["top_categories"]:
            tc, ta = cm["top_categories"][0]
            lines.append(
                f"• **{tc}** is your highest spending category (₹{ta:,.0f}). "
                f"A 20% reduction would save ≈₹{ta * 0.2:,.0f}/month."
            )
        over = [b for b in ctx["budgets"] if b["status"] == "over"]
        if over:
            cats_str = ", ".join(b["category"] for b in over)
            lines.append(f"• You have exceeded your budget in: **{cats_str}**. Review these categories.")
        if cm["savings_rate"] < 20:
            lines.append("• Your savings rate is below the recommended 20%. Prioritize cutting discretionary spending.")
        lines.append(
            "• Go to **Transactions** to review recent spending and identify patterns."
        )
        return "\n".join(lines)

    # ── Budget status ────────────────────────────────────────────────────────
    if any(w in q for w in ["budget", "overspend", "over budget", "budget status", "how much budget"]):
        if not ctx["budgets"]:
            return (
                "You have no budgets set for this month. "
                "Go to **Budgets** to set monthly spending limits per category.\n\n"
                f"This month you spent ₹{cm['expenses']:,.0f} without any budget limits."
            )
        over = [b for b in ctx["budgets"] if b["status"] == "over"]
        near = [b for b in ctx["budgets"] if b["status"] == "near"]
        ok = [b for b in ctx["budgets"] if b["status"] == "ok"]
        parts: list[str] = [f"**Budget Status for {cm['name']}:**"]
        if over:
            parts.append("🔴 **Over budget:**")
            for b in over:
                parts.append(f"  • {b['category']}: ₹{b['spent']:,.0f} / ₹{b['limit']:,.0f} ({b['pct']:.0f}%)")
        if near:
            parts.append("🟡 **Near limit (≥80%):**")
            for b in near:
                parts.append(f"  • {b['category']}: ₹{b['spent']:,.0f} / ₹{b['limit']:,.0f} ({b['pct']:.0f}%)")
        if ok:
            parts.append("🟢 **Within budget:**")
            for b in ok:
                parts.append(f"  • {b['category']}: ₹{b['spent']:,.0f} / ₹{b['limit']:,.0f} ({b['pct']:.0f}%)")
        return "\n".join(parts)

    # ── Income ───────────────────────────────────────────────────────────────
    if any(w in q for w in ["income", "earn", "salary", "how much did i earn", "how much income"]):
        if not has_income:
            return _no_data_msg("income entries", "Transactions")
        return (
            f"Your recorded income in {cm['name']} is ₹{cm['income']:,.0f}.\n"
            f"Expenses: ₹{cm['expenses']:,.0f} | Net savings: ₹{cm['net_savings']:,.0f} "
            f"({cm['savings_rate']:.1f}% rate)."
        )

    # ── Savings goals ────────────────────────────────────────────────────────
    if any(w in q for w in ["goal", "target", "saving for", "on track", "progress"]):
        if not ctx["goals"]:
            return "You have no active savings goals. Create one in the **Savings Goals** section."
        lines = [f"**Your {len(ctx['goals'])} active savings goal(s):**"]
        for g in ctx["goals"][:5]:
            extra = f" (need ₹{g['monthly_needed']:,.0f}/mo)" if g.get("monthly_needed") else ""
            lines.append(
                f"• **{g['name']}**: ₹{g['saved']:,.0f} / ₹{g['target']:,.0f} "
                f"— {g['pct']:.0f}% complete{extra}"
            )
        return "\n".join(lines)

    # ── Bills ────────────────────────────────────────────────────────────────
    if any(w in q for w in ["bill", "subscription", "recurring", "due", "upcoming", "payment"]):
        if not ctx["bills"]:
            return "No recurring bills tracked. Add bills in the **Bills** section."
        lines = [
            f"You have **{len(ctx['bills'])} active bill(s)** with an estimated "
            f"monthly total of ₹{ctx['monthly_bills_total']:,.0f}:",
        ]
        for b in ctx["bills"][:5]:
            due = f" — due {b['next_due']}" if b.get("next_due") else ""
            lines.append(f"• {b['name']}: ₹{b['amount']:,.0f} ({b['frequency']}){due}")
        return "\n".join(lines)

    # ── Spending habits ──────────────────────────────────────────────────────
    if any(w in q for w in ["spending habit", "analyze", "pattern", "habit"]):
        if not has_expenses:
            return _no_data_msg("expense transactions", "Transactions")
        lines = [f"**Spending analysis for {cm['name']}:**"]
        if cm["top_categories"]:
            lines.append("\nTop categories:")
            for c, a in cm["top_categories"][:5]:
                pct = a / cm["expenses"] * 100 if cm["expenses"] > 0 else 0
                lines.append(f"• {c}: ₹{a:,.0f} ({pct:.0f}%)")
        if prev["expenses"] > 0:
            change = (cm["expenses"] - prev["expenses"]) / prev["expenses"] * 100
            direction = "increased" if change > 0 else "decreased"
            lines.append(
                f"\nVs last month: total spending {direction} by {abs(change):.1f}% "
                f"(₹{prev['expenses']:,.0f} → ₹{cm['expenses']:,.0f})."
            )
        return "\n".join(lines)

    # ── Default: monthly snapshot ────────────────────────────────────────────
    lines = [
        f"**{cm['name']} snapshot:**",
        f"• Income: ₹{cm['income']:,.0f}",
        f"• Expenses: ₹{cm['expenses']:,.0f}",
        f"• Net savings: ₹{cm['net_savings']:,.0f} ({cm['savings_rate']:.1f}%)",
        f"• Transactions recorded: {cm['transaction_count']}",
    ]
    if ctx["budgets"]:
        over_count = sum(1 for b in ctx["budgets"] if b["status"] == "over")
        lines.append(
            f"• Budgets: {len(ctx['budgets'])} set, "
            f"{over_count} over budget"
        )
    if ctx["goals"]:
        lines.append(f"• Active savings goals: {len(ctx['goals'])}")
    lines.append(
        "\nTry asking: *Summarize my finances*, *Which category costs me most?*, "
        "*What is my budget status?*, or *Am I on track with my goals?*"
    )
    return "\n".join(lines)


def _deterministic_general(question: str) -> str:
    """Minimal rule-based fallback for general mode when no LLM is available."""
    q = question.lower()

    if any(w in q for w in ["compound interest", "compound"]):
        return (
            "**Compound interest** means you earn interest on both your principal *and* "
            "on the interest already earned.\n\n"
            "**Example (hypothetical):** ₹10,000 at 8% p.a. compounded annually:\n"
            "- Year 1: ₹10,800\n- Year 2: ₹11,664\n- Year 5: ₹14,693\n- Year 10: ₹21,589\n\n"
            "The longer you stay invested, the faster your money grows — this is why starting "
            "early matters so much.\n\n"
            "ℹ️ This is educational information, not certified financial advice."
        )

    if any(w in q for w in ["emergency fund", "emergency"]):
        return (
            "**Emergency fund** — a reserve of 3–6 months of living expenses held in a "
            "liquid account (savings or FD).\n\n"
            "**Why it matters:** Covers job loss, medical bills, or urgent repairs without "
            "going into debt.\n\n"
            "**How to build one (hypothetical):**\n"
            "- Monthly expenses: ₹30,000 → target ₹90,000–₹1,80,000\n"
            "- Save ₹5,000/month → fully funded in 18–36 months\n\n"
            "ℹ️ This is educational information, not certified financial advice."
        )

    if any(w in q for w in ["50/30/20", "budget rule", "budgeting rule"]):
        return (
            "**The 50/30/20 rule** divides after-tax income into three buckets:\n\n"
            "| Bucket | % | Examples |\n"
            "|--------|---|----------|\n"
            "| Needs | 50% | Rent, groceries, utilities, EMIs |\n"
            "| Wants | 30% | Dining out, streaming, travel |\n"
            "| Savings/Debt | 20% | Emergency fund, investments, loan repayment |\n\n"
            "**Hypothetical example:** Monthly take-home ₹60,000 → "
            "₹30,000 needs / ₹18,000 wants / ₹12,000 savings.\n\n"
            "ℹ️ This is educational information, not certified financial advice."
        )

    if any(w in q for w in ["inflation"]):
        return (
            "**Inflation** is the rate at which prices rise over time, reducing the "
            "purchasing power of money.\n\n"
            "**Example (hypothetical):** At 6% annual inflation, ₹1,00,000 today buys "
            "goods worth only ₹74,409 in 5 years.\n\n"
            "**What to do:** Keep investments that beat inflation (e.g., equity mutual "
            "funds, PPF, ELSS) rather than leaving large amounts idle in a savings account.\n\n"
            "ℹ️ This is educational information, not certified financial advice."
        )

    if any(w in q for w in ["debt", "loan", "emi", "repay"]):
        return (
            "**Debt repayment strategies:**\n\n"
            "• **Avalanche method** — pay minimums on all debts, then extra cash to the "
            "highest-interest debt first. Saves the most interest overall.\n"
            "• **Snowball method** — pay off the smallest balance first for quick wins "
            "and motivation.\n\n"
            "**Hypothetical example:** You have a ₹50,000 credit-card balance at 36% p.a. "
            "— paying only the minimum keeps you in debt for years. Paying ₹5,000 extra "
            "per month clears it in ~11 months and saves ₹8,000+ in interest.\n\n"
            "ℹ️ This is educational information, not certified financial advice."
        )

    if any(w in q for w in ["saving vs invest", "save vs invest", "difference between saving", "saving or invest", "invest vs sav"]):
        return (
            "**Saving vs Investing — what's the difference?**\n\n"
            "| | Saving | Investing |\n"
            "|---|---|---|\n"
            "| Purpose | Short-term goals, emergencies | Long-term wealth building |\n"
            "| Risk | Very low | Medium–High |\n"
            "| Return | Low (savings account/FD rate) | Potentially higher |\n"
            "| Liquidity | High — money accessible fast | Varies (stocks, mutual funds) |\n"
            "| Example | Emergency fund, holiday fund | SIP, stocks, PPF, NPS |\n\n"
            "**Rule of thumb:** Build 3–6 months of expenses in savings first, "
            "then start investing the surplus.\n\n"
            "ℹ️ This is educational information, not certified financial advice."
        )

    if any(w in q for w in ["create a budget", "how to budget", "make a budget", "monthly budget", "start budgeting", "set up a budget"]):
        return (
            "**How to create a monthly budget (step by step):**\n\n"
            "1. **Calculate take-home income** — your salary after tax and deductions.\n"
            "2. **List fixed expenses** — rent, EMIs, insurance premiums (amounts don't change).\n"
            "3. **List variable expenses** — groceries, transport, dining, entertainment.\n"
            "4. **Set spending limits** — apply the 50/30/20 split or your own percentages.\n"
            "5. **Track every rupee** — record transactions in FinAdvisor AI under Transactions.\n"
            "6. **Review at month end** — compare actual vs planned and adjust next month.\n\n"
            "**In FinAdvisor AI:** Go to **Budgets** → click **Add Budget** → choose a category, "
            "enter a monthly limit, and save. The app automatically tracks spending against each budget.\n\n"
            "ℹ️ This is educational information, not certified financial advice."
        )

    if any(w in q for w in ["best way to save", "ways to save", "how to save money", "tips to save", "save more money"]):
        return (
            "**Best ways to save money:**\n\n"
            "• **Pay yourself first** — transfer savings to a separate account as soon as income arrives.\n"
            "• **Automate savings** — set up a standing instruction for a fixed amount on salary day.\n"
            "• **Use the 50/30/20 rule** — allocate 20% of income to savings before spending on wants.\n"
            "• **Cut subscriptions you don't use** — review streaming, gym, and app subscriptions monthly.\n"
            "• **Cook more, eat out less** — dining out is often the highest discretionary expense.\n"
            "• **Avoid impulse purchases** — apply a 24-hour rule before non-essential buys.\n"
            "• **Set specific goals** — having a target (e.g. ₹1,00,000 emergency fund) makes saving motivating.\n\n"
            "**In FinAdvisor AI:** Use **Savings Goals** to set a target and track your progress. "
            "Use **Budgets** to cap discretionary spending.\n\n"
            "ℹ️ This is educational information, not certified financial advice."
        )

    if any(w in q for w in ["financial discipline", "discipline", "financial habit", "money habit", "self control", "willpower"]):
        return (
            "**How to improve financial discipline:**\n\n"
            "• **Write down your goals** — a concrete goal (e.g. save ₹5 lakh in 3 years) makes "
            "short-term sacrifices feel purposeful.\n"
            "• **Budget every month** — tracking where money goes creates awareness that changes behavior.\n"
            "• **Separate wants from needs** — before a purchase ask: *do I need this or just want it?*\n"
            "• **Remove friction from saving** — make it automatic so willpower is not required.\n"
            "• **Add friction to spending** — unlink saved cards from shopping apps; use cash for discretionary spend.\n"
            "• **Review monthly** — a 15-minute end-of-month review builds the habit of financial awareness.\n"
            "• **Celebrate small wins** — reaching a savings milestone is worth acknowledging.\n\n"
            "ℹ️ This is educational information, not certified financial advice."
        )

    if any(w in q for w in ["financial goal", "goals for future", "set goal", "future goal", "long term goal", "what goal"]):
        return (
            "**Financial goals to consider setting:**\n\n"
            "**Short-term (0–1 year):**\n"
            "• Build a 3-month emergency fund\n"
            "• Pay off credit-card debt\n"
            "• Save for a specific purchase\n\n"
            "**Medium-term (1–5 years):**\n"
            "• Down payment on a vehicle or home\n"
            "• Further education or skill development\n"
            "• 6-month emergency fund\n\n"
            "**Long-term (5+ years):**\n"
            "• Retirement corpus\n"
            "• Children's education fund\n"
            "• Passive income through investments\n\n"
            "**How to set them in FinAdvisor AI:** Go to **Savings Goals** → click **Add Goal** → "
            "enter the goal name, target amount, current amount, and optional target date. "
            "The app shows your progress and the monthly contribution needed.\n\n"
            "ℹ️ This is educational information, not certified financial advice."
        )

    # ── App navigation fallback ───────────────────────────────────────────────
    if any(w in q for w in [
        "how do i", "how to use", "where do i", "how can i add", "how to add",
        "dashboard", "transaction", "budget", "savings goal", "bills", "report",
        "family", "profile", "settings", "advisor", "health score", "insight",
        "login", "register", "sign up", "sign in", "log in",
    ]):
        return (
            "I can help you navigate FinAdvisor AI. Here are the main sections:\n\n"
            "• **Dashboard** — monthly summary (income, expenses, savings rate, health score)\n"
            "• **Transactions** — record income and expenses (click **Add Transaction**)\n"
            "• **Budgets** — set monthly spending limits per category (click **Add Budget**)\n"
            "• **Savings Goals** — track targets like emergency fund or a purchase (click **Add Goal**)\n"
            "• **Bills** — manage recurring payments and due dates (click **Add Bill**)\n"
            "• **AI Advisor** — Finance Chat (general education) · My Finances (personal, requires login)\n"
            "  · Insights (AI-generated cards from your data) · Health Score (0–100 score)\n"
            "• **Reports** — monthly reports, charts, and financial story\n"
            "• **Family Finance** — shared group finances with other users\n"
            "• **Profile** — update name, phone, income preference, and password\n"
            "• **Settings** — toggle dark mode and notification preferences\n\n"
            "Ask me a specific question like *How do I add a transaction?* or "
            "*How do I create a budget?* and I will give you step-by-step instructions."
        )

    return (
        "I'm FinAdvisor AI, your personal finance assistant. I can help with:\n\n"
        "• Budgeting strategies (50/30/20 rule, zero-based budgeting)\n"
        "• Saving and emergency fund planning\n"
        "• Understanding compound interest and inflation\n"
        "• Debt repayment strategies\n"
        "• Difference between saving and investing\n"
        "• Setting financial goals\n"
        "• How to use any part of FinAdvisor AI\n\n"
        "Try asking: *How does compound interest work?*, "
        "*What is the best way to save money?*, or *How do I add a transaction?*\n\n"
        "ℹ️ I provide educational information, not certified financial advice."
    )


# ---------------------------------------------------------------------------
# Public chat functions
# ---------------------------------------------------------------------------

def general_chat(history: list[dict]) -> dict:
    """
    Answer general personal-finance questions without any user DB data.

    Parameters
    ----------
    history : list of {"role": "user"|"assistant", "content": str}
        Full conversation so far, including the latest user message.

    Returns
    -------
    {"answer": str, "source": "openai"|"gemini"|"builtin"}
    """
    messages = _build_messages(_GENERAL_SYSTEM, history)
    answer, source = _call_llm(messages)
    if answer:
        return {"answer": answer, "source": source}

    # Deterministic fallback — use the last user message
    last_user = next(
        (m["content"] for m in reversed(history) if m.get("role") == "user"), ""
    )
    return {"answer": _deterministic_general(last_user), "source": "builtin"}


def personal_chat(user_id: int, history: list[dict]) -> dict:
    """
    Answer finance questions augmented with the authenticated user's real data.

    The user's financial snapshot is injected into the system prompt so the
    LLM can reference their actual income, expenses, budgets, goals, and bills.
    Falls back to general_chat if the DB lookup fails.

    Parameters
    ----------
    user_id : int
    history : list of {"role": "user"|"assistant", "content": str}

    Returns
    -------
    {"answer": str, "source": "openai"|"gemini"|"builtin"}
    """
    try:
        ctx = build_financial_context(user_id)
    except Exception:
        # If DB access fails, degrade gracefully to generic mode
        return general_chat(history)

    # Build a compact personal data summary for the system prompt
    cm = ctx["current_month"]
    data_lines: list[str] = [
        f"Current month: {cm['name']}",
        f"Income: ₹{cm['income']:,.0f}",
        f"Expenses: ₹{cm['expenses']:,.0f}",
        f"Net savings: ₹{cm['net_savings']:,.0f}",
        f"Savings rate: {cm['savings_rate']:.1f}%",
    ]

    if cm["top_categories"]:
        cats = ", ".join(f"{c} ₹{a:,.0f}" for c, a in cm["top_categories"])
        data_lines.append(f"Top spending categories: {cats}")

    prev = ctx["previous_month"]
    if prev["income"] > 0 or prev["expenses"] > 0:
        data_lines.append(
            f"Previous month: income ₹{prev['income']:,.0f}, "
            f"expenses ₹{prev['expenses']:,.0f}, "
            f"savings rate {prev['savings_rate']:.1f}%"
        )

    if ctx["budgets"]:
        bparts = []
        for b in ctx["budgets"]:
            status = {"over": "over budget", "near": "near limit", "ok": "on track"}[b["status"]]
            bparts.append(f"{b['category']}: ₹{b['spent']:,.0f}/₹{b['limit']:,.0f} ({status})")
        data_lines.append("Budgets: " + "; ".join(bparts))

    if ctx["goals"]:
        gparts = []
        for g in ctx["goals"][:5]:
            mn = f", need ₹{g['monthly_needed']:,.0f}/mo" if g.get("monthly_needed") else ""
            gparts.append(f"{g['name']} {g['pct']:.0f}% complete{mn}")
        data_lines.append("Savings goals: " + "; ".join(gparts))

    if ctx["bills"]:
        data_lines.append(
            f"Active bills: {len(ctx['bills'])} bills, "
            f"estimated monthly total ₹{ctx['monthly_bills_total']:,.0f}"
        )

    personal_data_str = "\n".join(data_lines)
    system = _GENERAL_SYSTEM + _PERSONAL_ADDENDUM.format(data=personal_data_str)
    messages = _build_messages(system, history)

    answer, source = _call_llm(messages)
    if answer:
        return {"answer": answer, "source": source}

    # Deterministic fallback using real user data
    last_user = next(
        (m["content"] for m in reversed(history) if m.get("role") == "user"), ""
    )
    return {"answer": _deterministic_personal(last_user, ctx), "source": "builtin"}


# ---------------------------------------------------------------------------
# Backwards-compatible wrapper (used by existing /advisor/chat route)
# ---------------------------------------------------------------------------

def chat_with_advisor(user_id: int, question: str, history: list[dict] | None = None) -> dict:
    """
    Legacy single-turn wrapper kept for backwards compatibility.
    New callers should use personal_chat() directly with full history.
    """
    if history is None:
        history = [{"role": "user", "content": question}]
    result = personal_chat(user_id, history)
    return {"answer": result["answer"], "source": result["source"], "context": {}}


# ---------------------------------------------------------------------------
# Financial context builder (unchanged public API)
# ---------------------------------------------------------------------------

def get_monthly_summary(user_id, month, year):
    txns = Transaction.query.filter_by(user_id=user_id).filter(
        extract("month", Transaction.date) == month,
        extract("year", Transaction.date) == year,
    ).all()
    income = sum(t.amount for t in txns if t.type == "income")
    expenses = sum(t.amount for t in txns if t.type == "expense")
    category_spending: dict[str, float] = defaultdict(float)
    for t in txns:
        if t.type == "expense":
            category_spending[t.category] += t.amount
    return {
        "income": income,
        "expenses": expenses,
        "net_savings": income - expenses,
        "savings_rate": (income - expenses) / income * 100 if income > 0 else 0,
        "category_spending": dict(category_spending),
        "transaction_count": len(txns),
        "transactions": txns,
    }


def build_financial_context(user_id: int) -> dict:
    """Collect the user's real financial data for AI context."""
    today = date.today()
    month, year = today.month, today.year
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1

    current = get_monthly_summary(user_id, month, year)
    previous = get_monthly_summary(user_id, prev_month, prev_year)

    budgets = Budget.query.filter_by(user_id=user_id, month=month, year=year).all()
    goals = SavingsGoal.query.filter_by(user_id=user_id, is_completed=False).all()
    bills = Bill.query.filter_by(user_id=user_id, is_active=True).all()

    budget_status = []
    for b in budgets:
        spent = current["category_spending"].get(b.category, 0)
        pct = spent / b.limit_amount * 100 if b.limit_amount > 0 else 0
        budget_status.append({
            "category": b.category,
            "limit": b.limit_amount,
            "spent": round(spent, 2),
            "pct": round(pct, 1),
            "status": "over" if pct > 100 else ("near" if pct >= 80 else "ok"),
        })

    bills_summary = [
        {
            "name": b.name,
            "amount": b.amount,
            "frequency": b.frequency,
            "next_due": b.next_due_date.isoformat() if b.next_due_date else None,
        }
        for b in bills
    ]
    monthly_bills = sum(
        b.amount if b.frequency == "monthly" else
        b.amount * 52 / 12 if b.frequency == "weekly" else
        b.amount / 12 if b.frequency == "yearly" else 0
        for b in bills
    )

    return {
        "current_month": {
            "name": date(year, month, 1).strftime("%B %Y"),
            "income": round(current["income"], 2),
            "expenses": round(current["expenses"], 2),
            "net_savings": round(current["net_savings"], 2),
            "savings_rate": round(current["savings_rate"], 1),
            "top_categories": sorted(
                current["category_spending"].items(), key=lambda x: -x[1]
            )[:5],
            "transaction_count": current["transaction_count"],
        },
        "previous_month": {
            "income": round(previous["income"], 2),
            "expenses": round(previous["expenses"], 2),
            "savings_rate": round(previous["savings_rate"], 1),
        },
        "budgets": budget_status,
        "goals": [
            {
                "name": g.name,
                "target": g.target_amount,
                "saved": g.current_amount,
                "pct": round(
                    g.current_amount / g.target_amount * 100
                    if g.target_amount > 0 else 0,
                    1,
                ),
                "monthly_needed": g.to_dict().get("monthly_needed"),
            }
            for g in goals
        ],
        "bills": bills_summary,
        "monthly_bills_total": round(monthly_bills, 2),
    }


# ---------------------------------------------------------------------------
# Insights engine (unchanged)
# ---------------------------------------------------------------------------

def generate_insights(user_id: int) -> list[dict]:
    today = date.today()
    month, year = today.month, today.year
    insights: list[dict] = []

    current = get_monthly_summary(user_id, month, year)
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    previous = get_monthly_summary(user_id, prev_month, prev_year)

    income = current["income"]
    expenses = current["expenses"]
    net_savings = current["net_savings"]
    savings_rate = current["savings_rate"]
    cat_spending = current["category_spending"]

    if current["transaction_count"] < 3:
        insights.append({
            "title": "Add More Transactions",
            "message": "Add at least a few transactions this month to get personalized insights.",
            "insight_type": "info",
            "priority": "medium",
            "action_label": "Add Transaction",
            "action_url": "/transactions",
        })
        return insights

    # Savings rate
    if savings_rate >= 30:
        insights.append({
            "title": "Excellent Savings Rate!",
            "message": f"Savings rate this month: {savings_rate:.1f}% — ₹{net_savings:,.0f} saved. Excellent!",
            "insight_type": "savings", "priority": "low",
        })
    elif savings_rate >= 20:
        insights.append({
            "title": "Good Savings Rate",
            "message": f"Savings rate: {savings_rate:.1f}% (₹{net_savings:,.0f} from ₹{income:,.0f}). Try to push above 30%.",
            "insight_type": "savings", "priority": "low",
        })
    elif savings_rate >= 10:
        insights.append({
            "title": "Savings Rate Below Recommended Level",
            "message": f"Savings rate is {savings_rate:.1f}%. Experts recommend at least 20%.",
            "insight_type": "savings", "priority": "medium",
            "action_label": "Review Expenses", "action_url": "/transactions",
        })
    elif income > 0 and savings_rate <= 0:
        insights.append({
            "title": "Spending Exceeds Income — Critical",
            "message": f"Expenses (₹{expenses:,.0f}) exceed income (₹{income:,.0f}) by ₹{abs(net_savings):,.0f}.",
            "insight_type": "spending", "priority": "critical",
            "action_label": "Review Budget", "action_url": "/budgets",
        })
    else:
        insights.append({
            "title": "Low Savings Rate",
            "message": f"Savings rate: {savings_rate:.1f}%. Consider the 50/30/20 rule.",
            "insight_type": "savings", "priority": "high",
            "action_label": "Set a Budget", "action_url": "/budgets",
        })

    # Largest category
    if cat_spending:
        top_cat = max(cat_spending, key=cat_spending.get)
        top_amount = cat_spending[top_cat]
        pct = (top_amount / expenses * 100) if expenses > 0 else 0
        insights.append({
            "title": f"Top Spending: {top_cat}",
            "message": f"{top_cat} is your largest expense at ₹{top_amount:,.0f} ({pct:.0f}% of total).",
            "insight_type": "spending", "priority": "medium", "category": top_cat,
        })

    # Budget alerts
    budgets = Budget.query.filter_by(user_id=user_id, month=month, year=year).all()
    for b in budgets:
        spent = cat_spending.get(b.category, 0)
        utilization = (spent / b.limit_amount * 100) if b.limit_amount > 0 else 0
        if utilization > 100:
            over_by = spent - b.limit_amount
            insights.append({
                "title": f"Over Budget: {b.category}",
                "message": f"{b.category} budget exceeded by ₹{over_by:,.0f} (₹{spent:,.0f} vs ₹{b.limit_amount:,.0f}).",
                "insight_type": "budget", "priority": "high", "category": b.category,
                "action_label": "View Budget", "action_url": "/budgets",
            })
        elif utilization >= 90:
            insights.append({
                "title": f"Budget Almost Exhausted: {b.category}",
                "message": f"Used {utilization:.0f}% of {b.category} budget. ₹{b.limit_amount - spent:,.0f} remaining.",
                "insight_type": "budget", "priority": "high", "category": b.category,
                "action_label": "View Budget", "action_url": "/budgets",
            })
        elif utilization >= 75:
            insights.append({
                "title": f"Budget Warning: {b.category}",
                "message": f"Used {utilization:.0f}% of {b.category} budget (₹{spent:,.0f} / ₹{b.limit_amount:,.0f}).",
                "insight_type": "budget", "priority": "medium", "category": b.category,
                "action_label": "View Budget", "action_url": "/budgets",
            })

    # Month-over-month spending spikes
    if previous["expenses"] > 0 and current["expenses"] > 0:
        prev_cat = previous["category_spending"]
        for cat, current_amt in cat_spending.items():
            prev_amt = prev_cat.get(cat, 0)
            if prev_amt > 0:
                change_pct = (current_amt - prev_amt) / prev_amt * 100
                if change_pct > 50 and current_amt > 2000:
                    insights.append({
                        "title": f"Spending Spike: {cat}",
                        "message": f"{cat} up {change_pct:.0f}% vs last month (₹{prev_amt:,.0f} → ₹{current_amt:,.0f}).",
                        "insight_type": "spending", "priority": "medium", "category": cat,
                    })

    # Goal reminders
    goals = SavingsGoal.query.filter_by(user_id=user_id, is_completed=False).all()
    for g in goals:
        gd = g.to_dict()
        if gd["progress_percent"] >= 90:
            insights.append({
                "title": f"Almost There: {g.name}",
                "message": f"'{g.name}' is {gd['progress_percent']:.0f}% complete! ₹{gd['remaining_amount']:,.0f} left.",
                "insight_type": "goal", "priority": "low",
            })
        elif gd.get("monthly_needed") and gd["monthly_needed"] > 0:
            insights.append({
                "title": f"Goal Reminder: {g.name}",
                "message": f"Save ₹{gd['monthly_needed']:,.0f}/month to reach '{g.name}' by {gd['target_date']}.",
                "insight_type": "goal", "priority": "medium",
            })

    # Emergency fund
    emergency = SavingsGoal.query.filter_by(user_id=user_id).filter(
        SavingsGoal.name.ilike("%emergency%")
    ).first()
    if not emergency and income > 0:
        recommended = expenses * 6 if expenses > 0 else income * 3
        insights.append({
            "title": "Set Up an Emergency Fund",
            "message": f"Experts recommend 3–6 months of expenses (≈₹{recommended:,.0f}) as an emergency fund.",
            "insight_type": "savings", "priority": "high",
            "action_label": "Create Goal", "action_url": "/goals",
        })

    # Upcoming bills
    upcoming_bills = Bill.query.filter_by(user_id=user_id, is_active=True).filter(
        Bill.next_due_date <= date.today() + timedelta(days=7),
        Bill.next_due_date >= date.today(),
    ).all()
    if upcoming_bills:
        total_due = sum(b.amount for b in upcoming_bills)
        names = ", ".join(b.name for b in upcoming_bills[:3])
        insights.append({
            "title": f"{len(upcoming_bills)} Bill(s) Due This Week",
            "message": f"Upcoming: {names}. Total: ₹{total_due:,.0f}.",
            "insight_type": "info", "priority": "high",
            "action_label": "View Bills", "action_url": "/bills",
        })

    # No budgets warning
    if not budgets and expenses > 0:
        insights.append({
            "title": "No Budgets Set This Month",
            "message": f"You spent ₹{expenses:,.0f} without any budgets.",
            "insight_type": "info", "priority": "medium",
            "action_label": "Create Budget", "action_url": "/budgets",
        })

    # Duplicate transaction detection
    seen: dict = {}
    for t in current.get("transactions", []):
        if t.type == "expense":
            key = (t.amount, t.category, t.date)
            if key in seen:
                insights.append({
                    "title": "Possible Duplicate Transaction",
                    "message": f"Two {t.category} transactions of ₹{t.amount:,.0f} on {t.date}. Verify.",
                    "insight_type": "info", "priority": "medium", "category": t.category,
                    "action_label": "Review Transactions", "action_url": "/transactions",
                })
                break
            seen[key] = True

    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    insights.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 2))
    return insights
