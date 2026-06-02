import os
import json
import html
from pathlib import Path
from urllib.parse import urljoin

import requests
import feedparser
from bs4 import BeautifulSoup


FEED_URL = os.getenv("RSS_FEED_URL", "https://varamama.com/listings/feed/")
STATE_FILE = Path(os.getenv("STATE_FILE", "posted_links.json"))
MAX_POSTS_PER_RUN = int(os.getenv("MAX_POSTS_PER_RUN", "3"))

POST_TO_TELEGRAM = os.getenv("POST_TO_TELEGRAM", "true").lower() == "true"
POST_TO_FACEBOOK = os.getenv("POST_TO_FACEBOOK", "false").lower() == "true"
POST_TO_BLOGGER = os.getenv("POST_TO_BLOGGER", "false").lower() == "true"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
FACEBOOK_GRAPH_API_VERSION = os.getenv("FACEBOOK_GRAPH_API_VERSION", "v25.0")

BLOGGER_CLIENT_ID = os.getenv("BLOGGER_CLIENT_ID", "")
BLOGGER_CLIENT_SECRET = os.getenv("BLOGGER_CLIENT_SECRET", "")
BLOGGER_REFRESH_TOKEN = os.getenv("BLOGGER_REFRESH_TOKEN", "")
BLOGGER_BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "")

PLATFORMS = {
    "telegram": POST_TO_TELEGRAM,
    "facebook": POST_TO_FACEBOOK,
    "blogger": POST_TO_BLOGGER,
}


class ConfigError(Exception):
    pass


def require_env(enabled, platform, variables):
    if not enabled:
        return

    missing = [name for name, value in variables.items() if not value]
    if missing:
        raise ConfigError(
            f"{platform} is enabled, but these environment variables/secrets are missing: "
            + ", ".join(missing)
        )


def validate_config():
    if not any(PLATFORMS.values()):
        raise ConfigError("No platform is enabled. Set at least one POST_TO_* value to true.")

    require_env(
        POST_TO_TELEGRAM,
        "Telegram",
        {
            "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
            "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        },
    )
    require_env(
        POST_TO_FACEBOOK,
        "Facebook",
        {
            "FACEBOOK_PAGE_ID": FACEBOOK_PAGE_ID,
            "FACEBOOK_PAGE_ACCESS_TOKEN": FACEBOOK_PAGE_ACCESS_TOKEN,
        },
    )
    require_env(
        POST_TO_BLOGGER,
        "Blogger",
        {
            "BLOGGER_CLIENT_ID": BLOGGER_CLIENT_ID,
            "BLOGGER_CLIENT_SECRET": BLOGGER_CLIENT_SECRET,
            "BLOGGER_REFRESH_TOKEN": BLOGGER_REFRESH_TOKEN,
            "BLOGGER_BLOG_ID": BLOGGER_BLOG_ID,
        },
    )


def load_posted_state():
    """Load posting state.

    Backward compatibility:
    - Old file format was a list of links already posted to Telegram.
    - New format is a dict: {link: {"telegram": true, "facebook": true, "blogger": true}}
    """
    if not STATE_FILE.exists():
        return {}

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if isinstance(data, list):
        return {str(link): {"telegram": True} for link in data if link}

    if isinstance(data, dict):
        normalized = {}
        for link, status in data.items():
            if isinstance(status, dict):
                normalized[str(link)] = {
                    "telegram": bool(status.get("telegram", False)),
                    "facebook": bool(status.get("facebook", False)),
                    "blogger": bool(status.get("blogger", False)),
                }
            elif isinstance(status, list):
                normalized[str(link)] = {name: name in status for name in PLATFORMS}
            elif isinstance(status, bool):
                normalized[str(link)] = {name: bool(status) for name in PLATFORMS}
        return normalized

    return {}


def save_posted_state(posted_state):
    ordered = {
        link: {
            "telegram": bool(status.get("telegram", False)),
            "facebook": bool(status.get("facebook", False)),
            "blogger": bool(status.get("blogger", False)),
        }
        for link, status in sorted(posted_state.items())
    }
    STATE_FILE.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")


def get_entry_link(entry):
    link = entry.get("link")
    if link:
        return link

    entry_id = entry.get("id")
    if entry_id:
        return entry_id

    return None


def get_image_url(entry):
    media_content = entry.get("media_content", [])
    if media_content:
        url = media_content[0].get("url")
        if url:
            return url

    media_thumbnail = entry.get("media_thumbnail", [])
    if media_thumbnail:
        url = media_thumbnail[0].get("url")
        if url:
            return url

    for link in entry.get("links", []):
        href = link.get("href")
        link_type = link.get("type", "")
        rel = link.get("rel", "")

        if href and (link_type.startswith("image/") or rel == "enclosure"):
            return href

    html_blocks = []

    if entry.get("summary"):
        html_blocks.append(entry.get("summary"))

    if entry.get("description"):
        html_blocks.append(entry.get("description"))

    for content_item in entry.get("content", []):
        value = content_item.get("value")
        if value:
            html_blocks.append(value)

    for block in html_blocks:
        soup = BeautifulSoup(block, "html.parser")
        img = soup.find("img")
        if img and img.get("src"):
            return urljoin(FEED_URL, img.get("src"))

    return None


def get_summary_text(entry, max_chars=500):
    html_blocks = []

    if entry.get("summary"):
        html_blocks.append(entry.get("summary"))

    if entry.get("description"):
        html_blocks.append(entry.get("description"))

    for content_item in entry.get("content", []):
        value = content_item.get("value")
        if value:
            html_blocks.append(value)

    for block in html_blocks:
        soup = BeautifulSoup(block, "html.parser")
        text = soup.get_text(" ", strip=True)
        if text:
            if len(text) > max_chars:
                return text[: max_chars - 3].rstrip() + "..."
            return text

    return ""


def build_telegram_message(entry, link):
    title = html.escape(entry.get("title", "নতুন লিস্টিং"))
    safe_link = html.escape(link)

    return (
        "🏠 <b>নতুন লিস্টিং</b>\n\n"
        f"<b>{title}</b>\n\n"
        "🔗 বিস্তারিত দেখুন:\n"
        f"{safe_link}"
    )


def build_facebook_message(entry, link):
    title = entry.get("title", "নতুন লিস্টিং")
    summary = get_summary_text(entry, max_chars=350)

    parts = [f"🏠 নতুন লিস্টিং\n\n{title}"]
    if summary:
        parts.append(summary)
    parts.append(f"বিস্তারিত দেখুন: {link}")
    return "\n\n".join(parts)


def build_blogger_content(entry, link):
    title = html.escape(entry.get("title", "নতুন লিস্টিং"))
    summary = html.escape(get_summary_text(entry, max_chars=1200)).replace("\n", "<br>")
    image_url = get_image_url(entry)

    blocks = [f"<h2>{title}</h2>"]

    if image_url:
        safe_image_url = html.escape(image_url, quote=True)
        blocks.append(f'<p><img src="{safe_image_url}" alt="{title}" style="max-width:100%;height:auto;"></p>')

    if summary:
        blocks.append(f"<p>{summary}</p>")

    safe_link = html.escape(link, quote=True)
    blocks.append(f'<p><a href="{safe_link}" target="_blank" rel="noopener">বিস্তারিত দেখুন</a></p>')
    return "\n".join(blocks)


def send_to_telegram(entry, link):
    message = build_telegram_message(entry, link)
    image_url = get_image_url(entry)

    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    if image_url:
        photo_response = requests.post(
            f"{base_url}/sendPhoto",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "photo": image_url,
                "caption": message,
                "parse_mode": "HTML",
            },
            timeout=30,
        )

        if photo_response.ok:
            print(f"Telegram posted with photo: {link}")
            return True

        print("Telegram sendPhoto failed. Trying sendMessage instead.")
        print(photo_response.text[:500])

    message_response = requests.post(
        f"{base_url}/sendMessage",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=30,
    )

    if message_response.ok:
        print(f"Telegram posted message: {link}")
        return True

    print("Telegram sendMessage failed.")
    print(message_response.text[:500])
    return False


def send_to_facebook(entry, link):
    url = f"https://graph.facebook.com/{FACEBOOK_GRAPH_API_VERSION}/{FACEBOOK_PAGE_ID}/feed"
    payload = {
        "message": build_facebook_message(entry, link),
        "link": link,
        "access_token": FACEBOOK_PAGE_ACCESS_TOKEN,
    }

    response = requests.post(url, data=payload, timeout=30)

    if response.ok:
        data = response.json()
        print(f"Facebook posted: {link} | post id: {data.get('id')}")
        return True

    print("Facebook post failed.")
    print(response.text[:1000])
    return False


def get_blogger_access_token():
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": BLOGGER_CLIENT_ID,
            "client_secret": BLOGGER_CLIENT_SECRET,
            "refresh_token": BLOGGER_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(f"Blogger access token refresh failed: {response.text[:1000]}")

    return response.json()["access_token"]


def send_to_blogger(entry, link):
    access_token = get_blogger_access_token()
    title = entry.get("title", "নতুন লিস্টিং")
    content = build_blogger_content(entry, link)

    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/"
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json={
            "kind": "blogger#post",
            "title": title,
            "content": content,
        },
        timeout=30,
    )

    if response.ok:
        data = response.json()
        print(f"Blogger posted: {link} | post url: {data.get('url')}")
        return True

    print("Blogger post failed.")
    print(response.text[:1000])
    return False


def platform_needs_post(posted_state, link, platform):
    if not PLATFORMS.get(platform):
        return False
    return not posted_state.get(link, {}).get(platform, False)


def entry_needs_any_enabled_platform(posted_state, link):
    return any(platform_needs_post(posted_state, link, platform) for platform in PLATFORMS)


def post_entry_to_enabled_platforms(entry, link, posted_state):
    posted_state.setdefault(link, {})

    if platform_needs_post(posted_state, link, "telegram"):
        posted_state[link]["telegram"] = send_to_telegram(entry, link)

    if platform_needs_post(posted_state, link, "facebook"):
        posted_state[link]["facebook"] = send_to_facebook(entry, link)

    if platform_needs_post(posted_state, link, "blogger"):
        posted_state[link]["blogger"] = send_to_blogger(entry, link)

    return posted_state[link]


def main():
    validate_config()
    posted_state = load_posted_state()

    feed = feedparser.parse(FEED_URL)

    if feed.bozo:
        print("Warning: RSS feed parse issue.")
        print(feed.bozo_exception)

    entries = feed.entries

    if not entries:
        print("No RSS entries found.")
        return

    new_entries = []

    for entry in reversed(entries):
        link = get_entry_link(entry)
        if link and entry_needs_any_enabled_platform(posted_state, link):
            new_entries.append(entry)

    if not new_entries:
        print("No new posts found for enabled platforms.")
        return

    posts_to_process = new_entries[:MAX_POSTS_PER_RUN]

    for entry in posts_to_process:
        link = get_entry_link(entry)
        if not link:
            print("Skipped: no link found")
            continue

        try:
            status = post_entry_to_enabled_platforms(entry, link, posted_state)
            print(f"Posting status for {link}: {status}")
        except Exception as exc:
            print(f"Failed while processing {link}: {exc}")
        finally:
            save_posted_state(posted_state)

    save_posted_state(posted_state)


if __name__ == "__main__":
    main()
