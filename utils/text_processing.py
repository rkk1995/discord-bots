import re
from typing import List

def split_for_discord(response: str, message_limit: int = 2000) -> List[str]:
    """Split a response into Discord-sized chunks without breaking formatting."""
    if len(response) <= message_limit:
        return [response]

    chunks: List[str] = []
    remaining = response

    while remaining:
        if len(remaining) <= message_limit:
            chunks.append(remaining)
            break

        slice_end = remaining.rfind("\n", 0, message_limit)
        if slice_end == -1 or slice_end < message_limit // 2:
            slice_end = remaining.rfind(" ", 0, message_limit)
        if slice_end == -1 or slice_end < message_limit // 2:
            slice_end = message_limit

        chunk = remaining[:slice_end].rstrip()
        if not chunk:
            chunk = remaining[: message_limit]
            slice_end = message_limit

        chunks.append(chunk)
        remaining = remaining[slice_end:].lstrip()

    return chunks

def clean_response(text: str) -> str:
    """Removes bot prefixes like '[Bot Name]:' or 'Name:' from the response."""
    # Regex to match pattern like "[Bot Grok]: " or "Grok: " at start of string
    # We use a flexible regex to catch variations
    
    # Check for [Bot ...] pattern specifically first as it's the main culprit
    text = re.sub(r"^\[Bot .*?\]:\s*", "", text)

    # Check for simple "Name:" pattern if it matches the bot's name or generic "Assistant:"
    # We can be a bit more aggressive if we assume the bot shouldn't start with "Name:" usually
    # unless it's a script format.
    # For now, let's stick to the [Bot ...] one which is the reported issue,
    # and maybe "Grok:" if it appears.
    text = re.sub(r"^Grok:\s*", "", text, flags=re.IGNORECASE)

    return text

def enforce_single_x_link(text: str) -> str:
    """Removes all but the first X/Twitter link from the text."""
    # Regex to find x.com or twitter.com links
    link_pattern = r"https?://(?:www\.)?(?:x\.com|twitter\.com)/[a-zA-Z0-9_/]+"

    links = list(re.finditer(link_pattern, text))

    if len(links) <= 1:
        return text

    # Keep the first link, remove the rest
    # We construct the new string by keeping everything up to the end of the first link
    # and then removing subsequent links from the remainder

    first_link_end = links[0].end()
    kept_part = text[:first_link_end]
    remainder = text[first_link_end:]

    # Remove subsequent links from remainder
    # We replace them with nothing
    for link in links[1:]:
        # We need to be careful with replacement to avoid messing up the text flow
        # But simply removing the URL is the safest strict enforcement
        # We use the specific match string to replace only that instance
        remainder = remainder.replace(link.group(), "")

    # Clean up potential double spaces or empty lines left behind
    remainder = re.sub(r"\n\s*\n", "\n", remainder)

    return kept_part + remainder
