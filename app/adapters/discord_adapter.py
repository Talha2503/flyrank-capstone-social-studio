import os
import httpx
from app.adapters.base import SocialPublisher

# in-memory idempotency guard: idempotency_key -> result
_published_keys: dict[str, dict] = {}


class DiscordPublisher(SocialPublisher):
    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if not self.webhook_url:
            raise RuntimeError("DISCORD_WEBHOOK_URL not set in .env")

    def publish(self, content: str, idempotency_key: str) -> dict:
        if idempotency_key in _published_keys:
            # already published under this key — do not post again
            return _published_keys[idempotency_key]

        resp = httpx.post(
            self.webhook_url,
            json={"content": content},
            params={"wait": "true"},  # ask Discord to return the message object
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        result = {
            "platform_message_id": str(data.get("id")),
            "url": None,
        }
        _published_keys[idempotency_key] = result
        return result