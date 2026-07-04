import json
from dataclasses import dataclass

MOCK_KB = {
    "billing": "Refunds available within 14 days if fewer than 100 API calls were made.",
    "technical": "Check API key permissions and rate limits in the dashboard settings page.",
    "account": "Password reset available via email link; MFA can be enabled in security settings.",
}


@dataclass
class Classification:
    category: str
    priority: str
    confidence: float


def classify_ticket(subject: str, body: str) -> Classification:
    text = f"{subject} {body}".lower()
    if any(w in text for w in ("refund", "billing", "invoice", "payment")):
        return Classification("billing", "medium", 0.88)
    if any(w in text for w in ("bug", "error", "crash", "api")):
        return Classification("technical", "high", 0.82)
    if any(w in text for w in ("password", "login", "account")):
        return Classification("account", "medium", 0.79)
    return Classification("general", "low", 0.55)


def tool_search_knowledge_base(category: str) -> str:
    return MOCK_KB.get(category, "No specific KB article found. Escalate to human support.")


def tool_get_user_plan(user_id: str) -> str:
    return json.dumps({"user_id": user_id, "plan": "pro", "quota_remaining": 8420})


def tool_create_draft(category: str, kb_snippet: str, body: str) -> str:
    return (
        f"Thank you for contacting support. Based on your {category} request: {kb_snippet} "
        f"We reviewed: {body[:120]}..."
    )
