def generate_variant(platform: str, post_body: str) -> str:
    """
    Template-based variant generation. Truncates/reformats the post body
    per platform style. No AI call — deterministic and free.
    """
    plain = " ".join(post_body.split())  # collapse whitespace/newlines

    if platform == "discord":
        snippet = plain[:1800]
        return f"{snippet}\n\n#update #devlog"

    if platform == "mock_x":
        snippet = plain[:230]
        return f"{snippet}... #tech"

    if platform == "mock_linkedin":
        snippet = plain[:2700]
        return (
            f"{snippet}\n\n"
            f"What are your thoughts on this? Let's discuss.\n"
            f"#technology #softwareengineering"
        )

    raise ValueError(f"unknown platform: {platform}")