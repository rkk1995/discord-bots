import re


# URL transformation function
def transform_url(url):
    """Transforms Twitter/X and Instagram URLs to fxtwitter/kkinstagram and cleans them."""
    original_url = url  # Keep original for comparison
    # Clean potential markdown escaping
    url = url.strip("<>")

    # If the URL is already transformed, just remove query params
    if any(
        domain in url
        for domain in ("fxtwitter.com", "kkinstagram.com", "ddinstagram.com")
    ):
        if "ddinstagram.com" in url:
            url = url.replace("ddinstagram.com", "kkinstagram.com")
        return re.sub(r"\?.*", "", url)

    # If it's an old vxtwitter link, convert it to fxtwitter
    if "vxtwitter.com" in url:
        url = url.replace("vxtwitter.com", "fxtwitter.com")

    # Change domain from x.com and twitter.com to fxtwitter.com if it's a status link
    # Make sure it actually contains /status/ to avoid transforming profile links etc.
    if ("x.com" in url or "twitter.com" in url) and "/status" in url:
        url = re.sub(
            r"https://(www\.)?(x\.com|twitter\.com)", "https://fxtwitter.com", url
        )

    # Change domain from instagram.com to kkinstagram.com if it's a post or reel link
    # Make sure it contains /p/ or /reel/
    if "instagram.com" in url and ("/p/" in url or "/reel/" in url):
        url = re.sub(r"https://(www\.)?instagram\.com", "https://kkinstagram.com", url)

    # Remove tracking parameters after the ? in URLs
    url = re.sub(r"\?.*", "", url)

    # Optional: remove trailing slash (fx/dd handle it fine usually, but consistency helps)
    url = url.rstrip("/")

    # If no transformation happened, return the cleaned original
    cleaned_original = re.sub(r"\?.*", "", original_url).rstrip("/")
    if url == cleaned_original:
        return cleaned_original

    return url


def handle_links(content: str) -> tuple[bool, str]:
    """
    Scans content for specific URLs and transforms them.
    Returns (True, transformed_content) if changes were made, (False, "") otherwise.
    """
    url_pattern = re.compile(
        r"<?(http[s]?://(?:www\.)?(?:x\.com|twitter\.com|instagram\.com|vxtwitter\.com|fxtwitter\.com|ddinstagram\.com|kkinstagram\.com)[^\s>]+)>?"
    )
    urls = url_pattern.findall(content)

    if not urls:
        return False, content

    original_to_transformed = {}
    for url in urls:
        new_url = transform_url(url)
        if new_url != url:
            original_to_transformed[url] = new_url

    if not original_to_transformed:
        return False, content

    final_content = content
    print("Transforming message content...")
    for original, transformed in original_to_transformed.items():
        # Escape original URL to handle potential special characters in regex
        final_content = re.sub(re.escape(original), transformed, final_content)
        print(f"  Replaced '{original}' with '{transformed}'")

    current_poster_display_name = message.author.display_name
    response_header = f"{current_poster_display_name} posted:"
    response_body = final_content

    full_response = f"{response_header}\n{response_body}"

    return True, full_response
