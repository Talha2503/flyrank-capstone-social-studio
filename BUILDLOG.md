# Build Log — AI Usage

This capstone was built with AI assistance (Claude) for scaffolding and
pairing, working entirely through the command line as I typed and ran every
command myself. This log records where AI helped, where it was wrong, and
what I changed or verified myself.

## Where AI helped

- Scaffolding the SQLAlchemy models (Post, Variant, Slot, PublishAttempt)
  and the initial FastAPI router structure.
- Suggesting the idempotency strategy: a deterministic sha256 key derived
  from variant_id + scheduled_at, checked against the database before any
  publish attempt, with each adapter also carrying a lighter in-process
  guard as defense in depth.
- Writing the constraint-profile validation logic and the template-based
  variant generator.
- Walking through Discord webhook setup (server creation, channel webhook,
  copying the URL into .env).

## Where AI was wrong / had to be fixed

- The variant generator originally raised a raw `ValueError` for an unknown
  platform, which was not caught anywhere in the router and crashed the
  request with a 500 Internal Server Error instead of a clean validation
  error. I caught this by testing the "rule-breaking variant" requirement
  live via curl. Fixed by adding an explicit known-platform check in the
  router before calling the generator, turning it into a proper 422 with
  a named violation.
- A notepad edit to `app/routers/posts.py` introduced a bad indentation
  level that crashed uvicorn on reload (`IndentationError: unexpected
  indent`). Instead of trying to patch the bad line, the whole file was
  rewritten cleanly to avoid further indentation drift.

## What I verified myself

- Every phase gate (design doc, ingestion + validation, review workflow,
  idempotent publish, durable scheduling) was tested live via curl against
  the running server, not just assumed from the code. The Discord message
  and the restart-survival test were confirmed by hand: watching the actual
  channel for duplicate messages and checking `/publish-history` after
  killing and restarting the server mid-wait.
- I can explain every endpoint, every model field, and the idempotency
  strategy (database-level check as source of truth, adapter-level check
  as a second layer) in my own words.