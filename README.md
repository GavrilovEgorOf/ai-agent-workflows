# support-triage

[![CI](https://github.com/GavrilovEgorOf/ai-agent-workflows/actions/workflows/ci.yml/badge.svg)](https://github.com/GavrilovEgorOf/ai-agent-workflows/actions/workflows/ci.yml)

**Support ticket pipeline** — classify the issue, pull from a small KB, draft a reply, ask a human if confidence is low.

Agent-as-workflow pipeline: every step is logged, token budget per ticket, approve/reject endpoint for low-confidence drafts.

## Flow

```
Ticket → classify (category, priority, confidence)
      → search_knowledge_base / get_user_plan
      → draft response
      → auto-send path OR pending_approval
      → audit log of each step
```

## API

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/tickets` | Create ticket and run pipeline |
| GET | `/tickets/{id}` | Ticket + full audit trail |
| POST | `/tickets/{id}/approval` | approve / reject / edit draft |

## Run

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

```bash
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"subject":"Billing","body":"I need a refund on last invoice"}'
```

## Tests

```bash
pytest -q
```

## Roadmap

See [ROADMAP.md](ROADMAP.md)

## License

MIT
