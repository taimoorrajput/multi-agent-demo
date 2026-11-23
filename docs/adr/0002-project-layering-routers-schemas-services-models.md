# ADR-0002: Project layering: routers, schemas, services, models

- **Status:** Accepted
- **Date:** 2026-11-23
- **Deciders:** Supervisor agent
- **Related tickets:** T-001, T-002, T-003, T-004, T-005

## Context
CLAUDE.md already prescribes a routers/schemas/services/models split, but doesn't pin down the
responsibility boundary between layers or how one feature's files are named. With 5 builders
working in parallel, an explicit, Accepted ADR removes ambiguity so the reviewer has an objective
check instead of a style debate per PR.

## Decision
Per feature `<feature>` (users, projects, tasks, tags, comments):
- `app/models/<feature>.py` — one SQLAlchemy model class, inherits the shared `Base` from
  `app/db.py`. No business logic.
- `app/schemas/<feature>.py` — Pydantic models: `<Feature>Create`, `<Feature>Update` (optional),
  `<Feature>Read` (the `response_model`). No ORM imports.
- `app/services/<feature>.py` — plain functions taking a `Session` plus typed args, doing the
  DB query/commit and raising `app.errors.ApiError` (see ADR-0003) on domain failures (not found,
  conflict). No FastAPI imports (keeps services testable without the app).
- `app/routers/<feature>.py` — one `APIRouter`, thin: parses request, calls the service, returns
  the typed response. Registered in `app/main.py` with exactly one `app.include_router(...)` line
  per ticket.
Each ticket's "Files in scope" is exactly these 4 files (+ its tests + its e2e test). Only
`app/db.py` (T-001-owned) and the single router-registration line in `app/main.py` are shared.

## Alternatives considered
- Option A (fat routers, no service layer): less boilerplate, but business logic ends up untestable
  without spinning up the app; rejected.
- Option B (one `models.py`/`schemas.py` file for everything): simpler for a tiny demo, but
  guarantees every ticket touches the same file and merge-conflicts; rejected — the whole point of
  5 parallel tickets is file isolation.

## Consequences
- Positive: predictable file layout per feature, reviewer can check scope mechanically, no two
  tickets touch the same model/schema/service/router file.
- Negative / trade-offs: slightly more files/boilerplate than a flat structure for a demo this size.
- Follow-ups: none expected; revisit if a feature needs cross-cutting logic (e.g. shared validators).
