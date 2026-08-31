# Design — Social Media Studio

## Problem
Turn one blog post into a scheduled multiplatform social campaign. The system
must generate platform-specific variants, enforce per-platform constraints,
route every variant through a human review step, and publish approved
variants exactly once — even under retries or a worker restart mid-batch.

## Data model

**Post**
- id (uuid, pk)
- source_type (url | markdown)
- source_content (text) — the original URL or pasted markdown
- body (text) — resolved/stored markdown, the single source of truth
- created_at

**Variant**
- id (uuid, pk)
- post_id (fk -> Post)
- platform (discord | mock_x | mock_linkedin)
- content (text)
- status (draft | approved | rejected | published)
- created_at
- updated_at

**Slot** (a scheduled publish time for a variant)
- id (uuid, pk)
- variant_id (fk -> Variant, unique with idempotency_key)
- scheduled_at (datetime)
- idempotency_key (string, unique) — deterministic, derived from variant_id + slot
- created_at

**PublishAttempt**
- id (uuid, pk)
- slot_id (fk -> Slot)
- status (success | failed)
- platform_message_id (string, nullable) — id/link of the live message
- error_message (text, nullable)
- attempted_at

## Constraint profiles (enforced in code, per platform)

| Platform | Max length | Tone | Hashtags |
|---|---|---|---|
| discord | 2000 chars | casual/community | 0-5 |
| mock_x | 280 chars | punchy/short | 1-3 |
| mock_linkedin | 3000 chars | professional | 2-5 |

Validation runs after generation, before a variant can leave `draft` status.
A variant that fails validation is never saved as reviewable — the API
returns an error naming the specific broken rule (e.g. "exceeds 280 char
limit for mock_x: got 310").

## SocialPublisher interface

```python
from abc import ABC, abstractmethod

class SocialPublisher(ABC):
    @abstractmethod
    def publish(self, content: str, idempotency_key: str) -> dict:
        """
        Publish content to the platform.
        Must be idempotent: calling twice with the same idempotency_key
        must not create a duplicate post.
        Returns: {"platform_message_id": str, "url": str | None}
        """
        ...
```

Implementations: `DiscordPublisher` (real, via webhook), `MockXPublisher`,
`MockLinkedInPublisher` (both record to a local `mock_publish_log` table and
return a fake message id). The app only ever calls `SocialPublisher.publish()`
— it never knows which concrete class it's talking to. Swapping platforms is
a config change (which adapter class to instantiate), not a code change to
business logic.

## API surface (high level)

- POST /posts — ingest a post (url or markdown)
- POST /posts/{id}/variants — generate variants for given platforms
- GET /variants/{id} — inspect a variant
- POST /variants/{id}/approve
- POST /variants/{id}/reject
- POST /variants/{id}/schedule — body: scheduled_at. 4xx if variant not approved
- GET /publish-history — list of PublishAttempt records

## Idempotency strategy

Each Slot gets a deterministic idempotency_key (e.g. hash of variant_id +
scheduled_at). The scheduler worker, before calling publish(), checks
PublishAttempt for an existing success record tied to that slot_id. If one
exists, it skips the call entirely — this makes retries and worker restarts
safe without relying on the adapter alone. The adapter's own idempotency_key
parameter is a second layer of defense for the real platform side.

## Non-goal

Image generation, analytics/engagement tracking, and real Instagram/X/LinkedIn
API integration are explicitly out of scope. Mock adapters plus one real free
platform (Discord) are sufficient to prove the architecture.