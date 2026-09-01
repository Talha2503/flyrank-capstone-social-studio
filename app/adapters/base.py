from abc import ABC, abstractmethod


class SocialPublisher(ABC):
    @abstractmethod
    def publish(self, content: str, idempotency_key: str) -> dict:
        """
        Publish content to the platform.
        Must be idempotent: calling twice with the same idempotency_key
        must not create a duplicate live post.
        Returns: {"platform_message_id": str, "url": str | None}
        """
        ...