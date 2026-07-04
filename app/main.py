from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.models import AuditStep, Base, Ticket
from app.services.workflow import run_triage

Path("data").mkdir(exist_ok=True)
engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Support Triage Agent — classify, tool calls, human approval, audit",
    lifespan=lifespan,
)


class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    user_id: str = "user-1"


class ApprovalRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|edit)$")
    edited_response: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name}


@app.post("/tickets")
async def create_ticket(body: TicketCreate, db: AsyncSession = Depends(get_db)):
    ticket = Ticket(subject=body.subject, body=body.body, user_id=body.user_id)
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    ticket = await run_triage(db, ticket)
    await db.commit()
    await db.refresh(ticket)
    return {
        "id": ticket.id,
        "status": ticket.status,
        "category": ticket.category,
        "priority": ticket.priority,
        "confidence": ticket.confidence,
        "draft_response": ticket.draft_response,
        "tokens_used": ticket.tokens_used,
    }


@app.get("/tickets")
async def list_tickets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).order_by(Ticket.id.desc()))
    tickets = result.scalars().all()
    return [
        {
            "id": t.id,
            "subject": t.subject,
            "status": t.status,
            "category": t.category,
            "confidence": t.confidence,
        }
        for t in tickets
    ]


@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    steps = await db.execute(select(AuditStep).where(AuditStep.ticket_id == ticket_id))
    return {
        "ticket": {
            "id": ticket.id,
            "subject": ticket.subject,
            "body": ticket.body,
            "status": ticket.status,
            "draft_response": ticket.draft_response,
            "tokens_used": ticket.tokens_used,
        },
        "audit_trail": [
            {"step": s.step, "detail": s.detail, "at": s.created_at.isoformat() if s.created_at else None}
            for s in steps.scalars().all()
        ],
    }


@app.post("/tickets/{ticket_id}/approval")
async def approve_ticket(ticket_id: int, body: ApprovalRequest, db: AsyncSession = Depends(get_db)):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    if ticket.status != "pending_approval":
        raise HTTPException(400, "Ticket not awaiting approval")

    if body.action == "approve":
        ticket.status = "approved"
    elif body.action == "reject":
        ticket.status = "rejected"
        ticket.draft_response = None
    else:
        ticket.status = "approved"
        ticket.draft_response = body.edited_response or ticket.draft_response

    db.add(AuditStep(ticket_id=ticket.id, step=f"human_{body.action}", detail=ticket.status))
    await db.commit()
    return {"id": ticket.id, "status": ticket.status, "draft_response": ticket.draft_response}
