CONSTRAINT_PROFILES = {
    "discord": {
        "max_length": 2000,
        "min_hashtags": 0,
        "max_hashtags": 5,
    },
    "mock_x": {
        "max_length": 280,
        "min_hashtags": 1,
        "max_hashtags": 3,
    },
    "mock_linkedin": {
        "max_length": 3000,
        "min_hashtags": 2,
        "max_hashtags": 5,
    },
}


def count_hashtags(text: str) -> int:
    return sum(1 for word in text.split() if word.startswith("#"))


def validate_variant(platform: str, content: str) -> list[str]:
    """
    Returns a list of human-readable violation messages.
    Empty list means the variant passes.
    """
    if platform not in CONSTRAINT_PROFILES:
        return [f"unknown platform: {platform}"]

    profile = CONSTRAINT_PROFILES[platform]
    violations = []

    length = len(content)
    if length > profile["max_length"]:
        violations.append(
            f"exceeds {profile['max_length']} char limit for {platform}: got {length}"
        )

    tag_count = count_hashtags(content)
    if tag_count < profile["min_hashtags"]:
        violations.append(
            f"needs at least {profile['min_hashtags']} hashtag(s) for {platform}: got {tag_count}"
        )
    if tag_count > profile["max_hashtags"]:
        violations.append(
            f"exceeds {profile['max_hashtags']} hashtag(s) for {platform}: got {tag_count}"
        )

    return violations