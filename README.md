# Multi-Agent Dev Team Kit — FastAPI edition (Claude Code)

A **Supervisor** plans and assigns work, **5+ Builders** code in parallel (one ticket = one branch = one PR), a **Reviewer** runs a review-fix loop (max 3 rounds), and a **merge gate** requires tests plus a recorded feature run. ADRs are written throughout.

```
                 ┌──────────────────────────┐
   feature ───▶  │ SUPERVISOR (no code)     │──▶ docs/adr/NNNN-*.md
   request       │ plans · tickets · unblock│──▶ .agents/tickets/T-00X.md
                 └────────────┬─────────────┘
          spawn-builders.sh   │  (git worktree + tmux pane per ticket)
     ┌──────────┬──────────┬──┴───────┬──────────┐
     ▼          ▼          ▼          ▼          ▼
  Builder1   Builder2   Builder3   Builder4   Builder5   → each opens 1 PR
     └──────────┴────┬─────┴──────────┴──────────┘
                     ▼  review-loop.sh (≤3 rounds)
               REVIEWER ⇄ BUILDER fix
                     ▼  verify-and-merge.sh
          tests ✔ + Playwright video ✔ + CI ✔ → squash merge
```

## Requirements → how this kit satisfies them

| Requirement | Mechanism |
|---|---|
| Supervisor never writes code | `.agents/settings/supervisor.json` **denies Edit/Write tools and git commit**. It can only run `./scripts/*` and `gh`. |
| 5+ parallel builders, isolated branches | `scripts/spawn-builders.sh` makes one `git worktree` + branch `feat/T-00X` per ticket and launches each builder in its own tmux pane. |
| One ticket = one PR | Builder prompt + `gh pr create` with `Closes T-00X` in title. |
| Reviewer loop, max 3 rounds | `scripts/review-loop.sh` — hard-coded `MAX_ROUNDS=3`, then escalates to supervisor. |
| Tests + recorded run before merge | `scripts/verify-and-merge.sh` runs ruff + pytest, then the ticket's e2e test, which starts the real API with uvicorn and clicks through **Swagger UI** with video recording on. It saves the evidence, waits for CI, then merges. |
| ADRs throughout | Supervisor writes ADRs while planning (`new-adr.sh`); builders add ADRs in PRs for design choices; reviewer rejects PRs that violate accepted ADRs. |

## Setup (once)

```bash
# prerequisites: git, gh (authenticated), tmux, jq, uv (or pip), claude (Claude Code CLI)
cp -r .agents docs scripts e2e .github CLAUDE.md  /path/to/your/fastapi-repo/
cd /path/to/your/fastapi-repo
chmod +x scripts/*.sh

# dev deps for tests + recorded e2e runs
uv add --dev pytest pytest-asyncio httpx ruff pytest-playwright
uv run playwright install --with-deps chromium

# edit CLAUDE.md: app module (default app.main:app), folder layout, DB/test commands
# if your app isn't app.main:app:  export APP_MODULE=yourpkg.main:app

# sanity check: adapt e2e/test_T000_example.py to one real endpoint, remove the skip line, then:
uv run pytest e2e -k T000 --video on --output /tmp/check && find /tmp/check -name '*.webm'

git add . && git commit -m "chore: add multi-agent kit" && git push
```

### How the recorded run works
`e2e/conftest.py` starts your app with uvicorn on a **random free port**, so 5 builders can run e2e tests
at the same time. It opens `/docs`, and the `swagger.call("POST", "/tasks", body=..., expect_status=201)`
helper expands the endpoint, clicks *Try it out*, fills params/body, clicks *Execute* and asserts the
status code. pytest-playwright saves a `.webm` video of all of it per test.

> If your app disables `/docs` in some environments, enable it when `ENV=test`.
> If tests need a database, point `DATABASE_URL` at a test DB (CI has a commented Postgres service).

## Run order (this is also your recording script)

```bash
tmux new -s agents                 # start recording the screen here

# 1. Supervisor (pane 0). Give it the feature request / PRD.
./scripts/supervisor.sh
#   > "Build <feature>. Plan it, write ADRs, create at least 5 independent tickets."
#   It runs new-adr.sh, new-ticket.sh, then spawn-builders.sh itself.

# 2. Watch the board in another pane
watch -n 5 ./scripts/board.sh

# 3. When a builder is BLOCKED, the supervisor answers:
./scripts/unblock.sh T-003 "Use the existing AuthContext, see ADR-0002"

# 4. For each PR that is opened:
./scripts/review-loop.sh T-001       # reviewer ⇄ builder, max 3 rounds
./scripts/verify-and-merge.sh T-001  # tests + video + CI → merge
```

## What to show on camera (checklist)
- [ ] Supervisor trying/refusing to edit a file (permission denied) → proves "never writes code"
- [ ] `docs/adr/` being created during planning
- [ ] 5 tmux panes with builders working at the same time
- [ ] `git worktree list` + `gh pr list` showing 5 branches / 5 PRs
- [ ] One PR going through ≥2 review rounds (comments visible on GitHub)
- [ ] A blocked builder being unblocked by the supervisor
- [ ] pytest passing + the Swagger UI e2e video playing + PR merged
- [ ] Final `git log --oneline` on main

## Tips
- Pick tickets that touch **different files** (one router per ticket) so merges don't conflict.
- Only ONE ticket should own Alembic migrations / shared models; make the others depend on it.
- Router registration in `app/main.py` is the usual conflict point: one line per ticket, resolved on rebase.
- Merge in dependency order; after each merge, other builders run `git rebase origin/main`.
- Use `BUILDER_MODE=auto` in `spawn-builders.sh` to run builders with
  `--dangerously-skip-permissions` (only on a throwaway machine/container).
