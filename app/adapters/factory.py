from app.adapters.discord_adapter import DiscordPublisher
from app.adapters.mock_adapters import MockXPublisher, MockLinkedInPublisher

_ADAPTERS = {
    "discord": DiscordPublisher,
    "mock_x": MockXPublisher,
    "mock_linkedin": MockLinkedInPublisher,
}


def get_publisher(platform: str):
    if platform not in _ADAPTERS:
        raise ValueError(f"no publisher registered for platform: {platform}")
    return _ADAPTERS[platform]()