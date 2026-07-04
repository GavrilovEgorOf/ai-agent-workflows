from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import AuditStep, Ticket
from app.services.agent import (
    classify_ticket,
    tool_create_draft,
    tool_get_user_plan,
    tool_search_knowledge_base,
)


async def log_step(session: AsyncSession, ticket_id: int, step: str, detail: str) -> None:
    session.add(AuditStep(ticket_id=ticket_id, step=step, detail=detail))


async def run_triage(session: AsyncSession, ticket: Ticket) -> Ticket:
    classification = classify_ticket(ticket.subject, ticket.body)
    ticket.category = classification.category
    ticket.priority = classification.priority
    ticket.confidence = classification.confidence
    ticket.tokens_used += 50
    await log_step(
        session,
        ticket.id,
        "classify",
        f"category={classification.category} priority={classification.priority} confidence={classification.confidence}",
    )

    kb = tool_search_knowledge_base(classification.category)
    ticket.tokens_used += 30
    await log_step(session, ticket.id, "tool_search_knowledge_base", kb)

    plan = tool_get_user_plan(ticket.user_id)
    ticket.tokens_used += 20
    await log_step(session, ticket.id, "tool_get_user_plan", plan)

    draft = tool_create_draft(classification.category, kb, ticket.body)
    ticket.tokens_used += 80
    ticket.draft_response = draft
    await log_step(session, ticket.id, "tool_create_response_draft", draft[:200])

    if ticket.tokens_used > settings.max_tokens_per_ticket:
        ticket.status = "blocked_cost_limit"
        await log_step(session, ticket.id, "cost_limit", "Token limit exceeded")
        return ticket

    if classification.confidence < settings.confidence_threshold:
        ticket.status = "pending_approval"
        await log_step(session, ticket.id, "human_approval_required", "Low confidence")
    else:
        ticket.status = "auto_drafted"
        await log_step(session, ticket.id, "auto_draft", "High confidence — draft ready")

    return ticket
