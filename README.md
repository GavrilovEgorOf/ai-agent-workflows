# AI Agent Workflows

[![CI](https://github.com/GavrilovEgorOf/ai-agent-workflows/actions/workflows/ci.yml/badge.svg)](https://github.com/GavrilovEgorOf/ai-agent-workflows/actions/workflows/ci.yml)

AI **Support Triage Agent** — production-style workflow automation with tool calling, retries, human approval, structured outputs, audit logs and cost limits.

## Workflow

```
Ticket received → classify → retrieve knowledge → draft answer → validate confidence
→ human approval if low confidence → audit log → final response
```

## Features

- `POST /tickets` — create ticket and run triage workflow
- Structured classification: category, priority, confidence
- Tool layer: `search_knowledge_base`, `get_user_plan`, `create_response_draft`
- Human approval: `POST /tickets/{id}/approval` (approve/reject/edit)
- Token/cost limit per ticket
- Full audit trail per agent step

## Quick Start

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

```bash
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"subject":"API error","body":"My API key returns 429 rate limit errors"}'
```

## What This Proves

Agents in production are **workflows with control and logs**, not magic prompts.

## License

MIT
