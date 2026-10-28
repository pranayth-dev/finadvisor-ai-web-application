import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from ..models import FinancialInsight, ChatMessage
from ..extensions import db
from ..services.advisor import (
    build_financial_context,
    generate_insights,
    chat_with_advisor,
    general_chat,
    personal_chat,
)
from ..routes.dashboard import calculate_health_score
from datetime import date, datetime

advisor_bp = Blueprint("advisor", __name__)


def get_current_user_id():
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def _parse_history(data: dict) -> list[dict]:
    """
    Extract and validate conversation history from request JSON.
    Accepts either a 'history' list or a bare 'question' string.
    """
    history = data.get("history")
    if isinstance(history, list):
        clean = []
        for turn in history:
            if (
                isinstance(turn, dict)
                and turn.get("role") in ("user", "assistant")
                and isinstance(turn.get("content"), str)
                and turn["content"].strip()
            ):
                clean.append({"role": turn["role"], "content": turn["content"].strip()})
        if clean:
            return clean

    question = data.get("question", "")
    if isinstance(question, str) and question.strip():
        return [{"role": "user", "content": question.strip()}]

    return []


def _save_exchange(
    user_id: int | None,
    advisor_type: str,
    conversation_id: str,
    question: str,
    answer: str,
    ai_provider: str,
) -> None:
    """Persist one question/answer pair to the chat_messages table."""
    try:
        db.session.add(ChatMessage(
            user_id=user_id,
            advisor_type=advisor_type,
            conversation_id=conversation_id,
            role="user",
            content=question,
            ai_provider=None,
        ))
        db.session.add(ChatMessage(
            user_id=user_id,
            advisor_type=advisor_type,
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            ai_provider=ai_provider,
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROVIDER_LABELS = {
    "gemini": "Google Gemini 1.5 Flash",
    "openai": "OpenAI GPT-4o-mini",
    "builtin": "FinAdvisor Built-in Engine",
}


def _load_conversation_history(
    conversation_id: str,
    advisor_type: str,
    user_id: int | None,
    limit: int = 20,
) -> list[dict]:
    """
    Load saved conversation turns for context.
    For general chat user_id may be None, so we match on conversation_id only.
    Returns a list of {"role": ..., "content": ...} dicts.
    """
    try:
        q = ChatMessage.query.filter_by(
            conversation_id=conversation_id,
            advisor_type=advisor_type,
        )
        # If we have a user_id, only return that user's messages
        if user_id is not None:
            q = q.filter_by(user_id=user_id)
        rows = q.order_by(ChatMessage.created_at.asc()).limit(limit * 2).all()
        return [{"role": r.role, "content": r.content} for r in rows]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# General chat — no authentication required
# ---------------------------------------------------------------------------

@advisor_bp.route("/general-chat", methods=["POST"])
def general_chat_endpoint():
    """General financial literacy chatbot — no login required."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Please provide valid JSON data"}), 400

    # Accept either a bare question string or a full history list
    new_question = (data.get("question") or "").strip()
    if not new_question:
        # Fall back to last user message in a provided history list
        hist_raw = _parse_history(data)
        new_question = next(
            (m["content"] for m in reversed(hist_raw) if m["role"] == "user"), ""
        )
    if not new_question:
        return jsonify({"error": "question is required"}), 400
    if len(new_question) > 1000:
        return jsonify({"error": "Message too long (max 1000 characters)"}), 400

    conversation_id = data.get("conversation_id") or str(uuid.uuid4())

    # Optionally associate with authenticated user if a valid token is present
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_current_user_id()
    except Exception:
        pass

    # Build full history: saved turns + new question
    saved_history = _load_conversation_history(conversation_id, "general", user_id)
    # Avoid appending duplicate if the same question was already saved
    # (idempotency guard against accidental retries)
    if saved_history and saved_history[-1]["role"] == "user" and saved_history[-1]["content"] == new_question:
        history = saved_history
    else:
        history = saved_history + [{"role": "user", "content": new_question}]

    result = general_chat(history)

    # Only persist if this is genuinely a new exchange (not a retry of the last one)
    _save_exchange(
        user_id=user_id,
        advisor_type="general",
        conversation_id=conversation_id,
        question=new_question,
        answer=result["answer"],
        ai_provider=result["source"],
    )

    return jsonify({
        "answer": result["answer"],
        "source": result["source"],
        "ai_provider": _PROVIDER_LABELS.get(result["source"], result["source"]),
        "conversation_id": conversation_id,
        "note": (
            "This is educational information about personal finance. "
            "It is not certified financial advice."
        ),
    }), 200


# ---------------------------------------------------------------------------
# Personal chat — authentication required, injects real user data
# ---------------------------------------------------------------------------

@advisor_bp.route("/chat", methods=["POST"])
@jwt_required()
def chat():
    """Personalised chat using the authenticated user's real financial data."""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid user ID"}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Please provide valid JSON data"}), 400

    # Accept either a bare question string or a full history list
    new_question = (data.get("question") or "").strip()
    if not new_question:
        hist_raw = _parse_history(data)
        new_question = next(
            (m["content"] for m in reversed(hist_raw) if m["role"] == "user"), ""
        )
    if not new_question:
        return jsonify({"error": "question is required"}), 400
    if len(new_question) > 1000:
        return jsonify({"error": "Message too long (max 1000 characters)"}), 400

    conversation_id = data.get("conversation_id") or str(uuid.uuid4())

    # Load saved conversation turns for multi-turn context
    saved_history = _load_conversation_history(conversation_id, "personal", user_id)
    # Idempotency: don't add duplicate if this question is already the last turn
    if saved_history and saved_history[-1]["role"] == "user" and saved_history[-1]["content"] == new_question:
        history = saved_history
    else:
        history = saved_history + [{"role": "user", "content": new_question}]

    result = personal_chat(user_id, history)

    _save_exchange(
        user_id=user_id,
        advisor_type="personal",
        conversation_id=conversation_id,
        question=new_question,
        answer=result["answer"],
        ai_provider=result["source"],
    )

    return jsonify({
        "question": new_question,
        "answer": result["answer"],
        "source": result["source"],
        "ai_provider": _PROVIDER_LABELS.get(result["source"], result["source"]),
        "conversation_id": conversation_id,
        "note": (
            "This is informational guidance based on your financial data. "
            "Not certified financial advice."
        ),
    }), 200


# ---------------------------------------------------------------------------
# Conversation history
# ---------------------------------------------------------------------------

@advisor_bp.route("/messages", methods=["GET"])
@jwt_required()
def get_messages():
    """
    Return saved chat messages for the authenticated user.
    Query params:
      advisor_type  personal|general  (default: personal)
      conversation_id  filter to one conversation
      limit  max messages to return (default 100)
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid user ID"}), 401

    advisor_type = request.args.get("advisor_type", "personal")
    conversation_id = request.args.get("conversation_id")
    limit = min(int(request.args.get("limit", 100)), 200)

    query = ChatMessage.query.filter_by(user_id=user_id, advisor_type=advisor_type)
    if conversation_id:
        query = query.filter_by(conversation_id=conversation_id)

    messages = query.order_by(ChatMessage.created_at.asc()).limit(limit).all()
    return jsonify({"messages": [m.to_dict() for m in messages]}), 200


@advisor_bp.route("/conversations", methods=["GET"])
@jwt_required()
def list_conversations():
    """
    Return the distinct conversation IDs (most recent first) for the user.
    Each entry: {conversation_id, advisor_type, first_message, last_at, count}
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid user ID"}), 401

    advisor_type = request.args.get("advisor_type", "personal")

    rows = (
        db.session.query(
            ChatMessage.conversation_id,
            db.func.min(ChatMessage.content).label("first_message"),
            db.func.max(ChatMessage.created_at).label("last_at"),
            db.func.count(ChatMessage.id).label("count"),
        )
        .filter_by(user_id=user_id, advisor_type=advisor_type, role="user")
        .group_by(ChatMessage.conversation_id)
        .order_by(db.func.max(ChatMessage.created_at).desc())
        .limit(20)
        .all()
    )

    conversations = [
        {
            "conversation_id": r.conversation_id,
            "first_message": r.first_message,
            "last_at": r.last_at.isoformat() if r.last_at else None,
            "count": r.count,
        }
        for r in rows
    ]
    return jsonify({"conversations": conversations}), 200


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

@advisor_bp.route("/insights", methods=["GET"])
@jwt_required()
def get_insights():
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid user ID"}), 401

    insights = (
        FinancialInsight.query
        .filter_by(user_id=user_id)
        .order_by(FinancialInsight.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify({"insights": [i.to_dict() for i in insights]}), 200


@advisor_bp.route("/analyze", methods=["POST"])
@jwt_required()
def analyze():
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid user ID"}), 401

    today = date.today()
    raw_insights = generate_insights(user_id)
    saved = []

    # Fetch existing titles for this month to avoid duplicates
    existing_titles = set(
        i.title for i in FinancialInsight.query.filter_by(
            user_id=user_id, month=today.month, year=today.year
        ).with_entities(FinancialInsight.title).all()
    )

    for item in raw_insights:
        # Skip if an insight with this exact title already exists for this month
        if item["title"] in existing_titles:
            continue
        insight = FinancialInsight(
            user_id=user_id,
            title=item["title"],
            message=item["message"],
            insight_type=item.get("insight_type", "info"),
            priority=item.get("priority", "medium"),
            category=item.get("category"),
            action_label=item.get("action_label"),
            action_url=item.get("action_url"),
            month=today.month,
            year=today.year,
        )
        db.session.add(insight)
        existing_titles.add(item["title"])
        saved.append(item)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({
        "insights": saved,
        "count": len(saved),
        "generated_at": datetime.now().isoformat(),
        "note": (
            "Insights are generated by FinAdvisor AI's built-in rules engine "
            "using your actual data. They are informational and not certified financial advice."
        ),
    }), 200


@advisor_bp.route("/health-score", methods=["GET"])
@jwt_required()
def health_score():
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid user ID"}), 401
    return jsonify(calculate_health_score(user_id)), 200


@advisor_bp.route("/insights/<int:insight_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(insight_id):
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid user ID"}), 401

    insight = FinancialInsight.query.filter_by(
        id=insight_id, user_id=user_id
    ).first()
    if not insight:
        return jsonify({"error": "Insight not found"}), 404

    insight.is_read = True
    db.session.commit()
    return jsonify({"message": "Marked as read"}), 200


@advisor_bp.route("/insights/<int:insight_id>", methods=["DELETE"])
@jwt_required()
def delete_insight(insight_id):
    """Delete a single insight. Never deletes associated financial records."""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid user ID"}), 401

    insight = FinancialInsight.query.filter_by(
        id=insight_id, user_id=user_id
    ).first()
    if not insight:
        return jsonify({"error": "Insight not found"}), 404

    db.session.delete(insight)
    db.session.commit()
    return jsonify({"message": "Insight deleted"}), 200


@advisor_bp.route("/insights/<int:insight_id>", methods=["GET"])
@jwt_required()
def get_insight_detail(insight_id):
    """Return full detail for a single insight."""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid user ID"}), 401

    insight = FinancialInsight.query.filter_by(
        id=insight_id, user_id=user_id
    ).first()
    if not insight:
        return jsonify({"error": "Insight not found"}), 404

    return jsonify({"insight": insight.to_dict()}), 200


@advisor_bp.route("/context", methods=["GET"])
@jwt_required()
def financial_context():
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid user ID"}), 401
    return jsonify(build_financial_context(user_id)), 200
