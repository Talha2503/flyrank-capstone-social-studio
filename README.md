# Social Media Studio

Turns one blog post into a scheduled multiplatform social campaign. Generates
platform-specific variants, enforces per-platform rules, routes every variant
through human review, and publishes approved variants exactly once — even
under retries or a worker restart mid-batch.

## Architecture

```
[blog post: URL or markdown]
        |
        v
  ingest + store  --->  variant generator  --->  constraint validation
        |                                              |
        v                                              v
  review workflow: draft -> approved | rejected
        |
        v
  scheduler (APScheduler, durable, resumable)
        |
        v
  SocialPublisher interface
   +-- DiscordPublisher (real, via webhook)
   +-- MockXPublisher (records locally)
   +-- MockLinkedInPublisher (records locally)
        |
        v
  publish history: one slot = one post, always
```

## Idempotency

Every scheduled `Slot` has a deterministic `idempotency_key` (sha256 of
variant_id + scheduled_at). Before any publish attempt — whether triggered
manually or by the background scheduler — the system checks the database
for an existing successful `PublishAttempt` tied to that slot. If one
exists, the publish is skipped. This check lives in the database, not in
memory, so it survives process restarts. Each adapter also carries its own
in-process idempotency guard as a second layer.

## Stack

- Python + FastAPI
- SQLite (via SQLAlchemy)
- APScheduler (background worker, polls every 10s)
- Discord webhook (real publish target)
- Mock adapters for X and LinkedIn

## Run steps

```
git clone https://github.com/Talha2503/flyrank-capstone-social-studio.git
cd flyrank-capstone-social-studio
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` from `.env.example` and add your own Discord webhook URL:

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_id/your_token
```

Create tables:

```
python -m app.create_tables
```

Run the app:

```
uvicorn app.main:app --reload
```

API docs available at `http://127.0.0.1:8000/docs`.

## API surface

- `POST /posts` — ingest a post (url or markdown)
- `POST /posts/{id}/variants` — generate + validate variants for given platforms
- `GET /variants/{id}` — inspect a variant
- `POST /variants/{id}/approve` / `/reject`
- `POST /variants/{id}/schedule` — schedule an approved variant (4xx if not approved)
- `POST /slots/{id}/publish` — manually trigger publish (idempotent)
- `GET /publish-history` — all publish attempts and their results

The background scheduler also auto-publishes due slots every 10 seconds.

## Known limitations

- In-memory idempotency guard in adapters resets on restart (database-level
  guard is the real source of truth and does survive restarts)
- Discord is the only real platform integration; X and LinkedIn are mocked
  per the capstone's safe-targets rule
- No image generation, analytics, or engagement tracking (explicit non-goal)
```
