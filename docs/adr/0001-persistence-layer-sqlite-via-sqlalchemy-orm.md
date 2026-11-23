# ADR-0001: Persistence layer: SQLite via SQLAlchemy ORM

- **Status:** Accepted
- **Date:** 2026-11-23
- **Deciders:** Supervisor agent
- **Related tickets:** T-001, T-002, T-003, T-004, T-005

## Context
The Task Manager API needs persistent storage for users, projects, tasks, tags, and comments,
with relational data (ownership, foreign keys, many-to-many tags). This is a demo repo: setup
must be fast, require no external services, and still demonstrate real relational modeling and
migrations so 5 builders can each add a model without stepping on each other.

## Decision
Use **SQLAlchemy 2.0 ORM with a synchronous engine against a SQLite file** (`app.db` in the repo
root, ignored by git; `sqlite:///:memory:` or a temp file for tests). T-001 owns `app/db.py`,
which defines the single shared `Base`, `engine`, `SessionLocal`, and a `get_db` FastAPI
dependency. Every other ticket imports `Base`/`get_db` from `app/db.py` but defines its OWN model
class in its OWN file under `app/models/`. Cross-model foreign keys reference table names as
strings (e.g. `ForeignKey("users.id")`), never cross-import other tickets' model classes, so
builders can work in parallel without import-time coupling. Table creation happens via
`Base.metadata.create_all(engine)` on app startup (no Alembic for this demo — single ticket,
T-001, owns this call in `app/db.py`).

## Alternatives considered
- Option A (async SQLAlchemy + aiosqlite): more "production-grade" but adds driver complexity and
  async session plumbing that isn't needed for a 5-ticket demo; rejected for time-to-demo.
- Option B (Postgres via docker-compose): most production-like, but requires every builder's
  sandbox to have Postgres running; adds a shared-infra dependency that risks flaky parallel runs.
- Option C (Alembic migrations from the start): correct for a long-lived app, but for a from-scratch
  demo schema with no prior data, `create_all` is simpler and ticket-independent; revisit with an
  ADR superseding this one if the schema needs to evolve after the first release.

## Consequences
- Positive: zero external services, fast test startup (ephemeral SQLite), builders can add models
  independently without merge conflicts on migration files.
- Negative / trade-offs: no migration history; SQLite's relaxed FK enforcement needs
  `PRAGMA foreign_keys=ON` (set in `app/db.py`); sync sessions block the event loop per-request,
  acceptable at this scale.
- Follow-ups: if this app needs multi-process writers or production deployment, open a new ADR
  superseding this one to move to Postgres + Alembic + async sessions.
