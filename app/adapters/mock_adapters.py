import uuid
from app.adapters.base import SocialPublisher

# process-local log: list of dicts, each {"idempotency_key", "content", "message_id"}
mock_publish_log: list[dict] = []


class MockXPublisher(SocialPublisher):
    platform_name = "mock_x"

    def publish(self, content: str, idempotency_key: str) -> dict:
        existing = next(
            (e for e in mock_publish_log if e["idempotency_key"] == idempotency_key and e["platform"] == self.platform_name),
            None,
        )
        if existing:
            return {"platform_message_id": existing["message_id"], "url": None}

        message_id = f"mockx_{uuid.uuid4().hex[:10]}"
        mock_publish_log.append({
            "idempotency_key": idempotency_key,
            "content": content,
            "message_id": message_id,
            "platform": self.platform_name,
        })
        return {"platform_message_id": message_id, "url": None}


class MockLinkedInPublisher(SocialPublisher):
    platform_name = "mock_linkedin"

    def publish(self, content: str, idempotency_key: str) -> dict:
        existing = next(
            (e for e in mock_publish_log if e["idempotency_key"] == idempotency_key and e["platform"] == self.platform_name),
            None,
        )
        if existing:
            return {"platform_message_id": existing["message_id"], "url": None}

        message_id = f"mockli_{uuid.uuid4().hex[:10]}"
        mock_publish_log.append({
            "idempotency_key": idempotency_key,
            "content": content,
            "message_id": message_id,
            "platform": self.platform_name,
        })
        return {"platform_message_id": message_id, "url": None}