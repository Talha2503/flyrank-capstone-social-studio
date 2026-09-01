# Evidence

Proof for each Requirements checkbox (Section 5 of the capstone brief).

## Ingestion

Post created and stored via `POST /posts`:

```
curl -X POST http://127.0.0.1:8000/posts -H "Content-Type: application/json" -d "{\"source_type\": \"markdown\", \"source_content\": \"We just shipped a new idempotent scheduling system...\"}"
```
Response: `{"id":"4d27d6db-86d8-4d26-8318-654a2e0f0f17", ...}`

## Constraint profiles enforced

One post produced two valid, different variants:

```
curl -X POST http://127.0.0.1:8000/posts/4d27d6db-86d8-4d26-8318-654a2e0f0f17/variants -H "Content-Type: application/json" -d "{\"platforms\": [\"discord\", \"mock_x\"]}"
```
Response: two variants with different content/length for `discord` and `mock_x`.

A rule-breaking / invalid platform request is blocked before review with a named violation:

```
curl -X POST http://127.0.0.1:8000/posts/4d27d6db-86d8-4d26-8318-654a2e0f0f17/variants -H "Content-Type: application/json" -d "{\"platforms\": [\"doesnotexist\"]}"
```
Response: `422` — `{"detail":[{"platform":"doesnotexist","violations":["unknown platform: doesnotexist"]}]}`

## Review workflow

Scheduling an unapproved (draft) variant is refused with a 4xx:

```
curl -X POST http://127.0.0.1:8000/variants/673e4d84-4c91-42e4-bcdc-4819c194ae5b/schedule -H "Content-Type: application/json" -d "{\"scheduled_at\": \"2026-09-01T12:00:00\"}"
```
Response: `422` — `{"detail":"cannot schedule a variant with status 'draft'; only 'approved' variants can be scheduled"}`

After approval, the same variant schedules successfully:

```
curl -X POST http://127.0.0.1:8000/variants/673e4d84-4c91-42e4-bcdc-4819c194ae5b/approve
curl -X POST http://127.0.0.1:8000/variants/673e4d84-4c91-42e4-bcdc-4819c194ae5b/schedule -H "Content-Type: application/json" -d "{\"scheduled_at\": \"2026-09-01T12:00:00\"}"
```
Response: `200` — slot returned with `idempotency_key`.

## Adapter layer / adapter swap

One `SocialPublisher` ABC (`app/adapters/base.py`) with three implementations:
`DiscordPublisher` (real, via webhook), `MockXPublisher`, `MockLinkedInPublisher`.
The publish endpoint and scheduler both call `get_publisher(variant.platform)`
from `app/adapters/factory.py` — a single dict lookup. Swapping which
platform a variant targets is a data change (the `platform` field), not a
business-logic change; no code outside `app/adapters/` needs to change to
add or swap a platform.

## Idempotent publish

Manual publish of a scheduled slot:

```
curl -X POST http://127.0.0.1:8000/slots/20dd5b83-b31a-48da-9e32-90c829dfc0e9/publish
```
Response: `{"status":"published","platform_message_id":"1544359598205702324", ...}` —
real message confirmed live in Discord channel.

Same slot published again immediately:

```
curl -X POST http://127.0.0.1:8000/slots/20dd5b83-b31a-48da-9e32-90c829dfc0e9/publish
```
Response: `{"status":"already_published","platform_message_id":"1544359598205702324", ...}` —
same message id returned, no second message created in Discord.

## Durable scheduling (worker restart mid-wait)

A variant was approved and scheduled ~90 seconds out. Immediately after
scheduling (before the due time), the uvicorn process was killed (Ctrl+C)
and restarted. The scheduler resumed polling, and once the scheduled time
passed, published the slot exactly once:

```
curl http://127.0.0.1:8000/publish-history
```
Response includes:
```
{"publish_attempt_id":"b5ca8e77-89e6-4255-aa72-7e54fab060d5","slot_id":"56f77ec0-36ce-43a1-9cb7-9994b2c5b55e","variant_id":"4f855dee-2929-46a1-9f37-51e07109f52b","platform":"discord","status":"success","platform_message_id":"1544361659542282310","error_message":null,"attempted_at":"2026-09-01T15:01:52.467017"}
```
Only one success record exists for this slot. Discord shows exactly one
message for this test (see commit `abad3d4`, includes screenshot).

## Publish history

`GET /publish-history` returns every attempt with status, platform,
message id, and timestamp (see responses above) — each visible and
queryable.

## Secrets

`DISCORD_WEBHOOK_URL` lives only in `.env`, which is gitignored.
`.env.example` ships with a placeholder value only.
```

