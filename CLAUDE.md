# Project rules for ALL agents (FastAPI repo)

## Commands (edit for your repo)
- Install:          `uv sync`            (or: `pip install -r requirements.txt -r requirements-dev.txt`)
- Run API:          `uv run uvicorn app.main:app --reload`
- Unit/API tests:   `uv run pytest tests -q`
- Lint:             `uv run ruff check .`
- E2E, one ticket:  `uv run pytest e2e -k T001 --video on --output .agents/evidence/T-001/playwright`
- Migrations:       `uv run alembic revision --autogenerate -m "..."` then `uv run alembic upgrade head`

## Code conventions
- Routers live in `app/routers/<feature>.py` and are registered in `app/main.py`.
- Pydantic schemas live in `app/schemas/`, DB models in `app/models/`, business logic in `app/services/`.
- Every endpoint has typed request/response models, so it shows up correctly in Swagger UI (/docs).
- API tests use `httpx.AsyncClient` + `ASGITransport` (or FastAPI `TestClient`). No real network calls.
- Each ticket's e2e test is named `test_T00X_<what>` in `e2e/test_T00X_*.py`. Hyphens aren't allowed
  in Python names, so T-001 becomes T001.

## Team protocol
- Roles: SUPERVISOR (plans, never codes), BUILDER (one ticket), REVIEWER (reviews, never codes).
- Tickets live in `.agents/tickets/T-XXX.md`. Status files live in `.agents/status/T-XXX` in the
  MAIN checkout (`$AGENTS_HOME`), not in a worktree.
- Status values: TODO, IN_PROGRESS, BLOCKED: <question>, PR_OPEN #<n>, CHANGES_REQUESTED, APPROVED,
  ESCALATED, MERGED.
- One ticket = one branch `feat/T-XXX-<slug>` = one PR titled `T-XXX: <title>`.
- Never touch files outside the ticket's "Files in scope" without asking the supervisor.
- Shared files (`app/main.py` router registration, Alembic migrations) cause merge conflicts.
  Only touch them if the ticket says so. Keep router registration to a single added line.

## Architecture Decision Records
- ADRs live in `docs/adr/NNNN-title.md` (template: `docs/adr/0000-template.md`).
- Read all ADRs with status Accepted before starting work. Do not violate them.
- If you make a significant design choice (new library, data model, API shape, auth pattern),
  add a new ADR in the same PR with status Proposed.
