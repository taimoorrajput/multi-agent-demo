# ADR-0003: Error response envelope

- **Status:** Accepted
- **Date:** 2026-11-23
- **Deciders:** Supervisor agent
- **Related tickets:** T-001, T-002, T-003, T-004, T-005

## Context
Five builders will each raise not-found/validation/conflict errors. Without a pinned shape, five
tickets will produce five different JSON error bodies, which breaks a consistent Swagger/API
experience and makes the reviewer's job (ADR-0002) harder to check.

## Decision
All domain errors raised from `app/services/*.py` use a single `app.errors.ApiError(status_code,
code, message)` exception (defined once, in T-001's `app/db.py`-adjacent module `app/errors.py`,
owned by T-001). `app/main.py` (T-001) registers one `@app.exception_handler(ApiError)` that
returns:
```json
{"error": {"code": "<SCREAMING_SNAKE_CASE>", "message": "<human readable>"}}
```
with the exception's `status_code` (404 for not found, 409 for conflict, 400 for bad request).
FastAPI's built-in 422 validation errors are left as FastAPI's default shape (Pydantic's
`detail` array) — routers/services never need to construct 422s by hand. Every ticket imports
`ApiError` from `app/errors.py`; no ticket defines its own exception type or handler.

## Alternatives considered
- Option A (raise `HTTPException(detail=str)` per ticket): quickest, but produces 5 slightly
  different ad hoc detail strings/shapes with no machine-readable `code`; rejected.
- Option B (wrap even 422s in the same envelope via a custom validation handler): more uniform,
  but requires one more shared file every ticket must avoid touching and isn't needed for this
  demo's acceptance criteria; deferred.

## Consequences
- Positive: one consistent error shape across all 5 features, easy for the reviewer to verify,
  easy for e2e tests to assert on.
- Negative / trade-offs: 422s have a different shape than domain errors (acceptable; FastAPI
  default is well understood by any API consumer).
- Follow-ups: if the API needs client SDKs, consider unifying 422s under the same envelope in a
  follow-up ADR.
