import os
import json
import html
from pathlib import Path
from urllib.parse import urljoin

import requests
import feedparser
from bs4 import BeautifulSoup


FEED_URL = os.getenv("RSS_FEED_URL", "https://varamama.com/listings/feed/")
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

STATE_FILE = Path("posted_links.json")
MAX_POSTS_PER_RUN = int(os.getenv("MAX_POSTS_PER_RUN", "3"))


def load_posted_links():
    if not STATE_FILE.exists():
        return set()

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return set(data)
    except Exception:
        return set()


def save_posted_links(posted_links):
    STATE_FILE.write_text(
        json.dumps(sorted(posted_links), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


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


def build_message(entry, link):
    title = html.escape(entry.get("title", "নতুন লিস্টিং"))
    safe_link = html.escape(link)

    return (
        "🏠 <b>নতুন লিস্টিং</b>\n\n"
        f"<b>{title}</b>\n\n"
        "🔗 বিস্তারিত দেখুন:\n"
        f"{safe_link}"
    )


def send_to_telegram(entry):
    link = get_entry_link(entry)
    if not link:
        print("Skipped: no link found")
        return False, None

    message = build_message(entry, link)
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
            print(f"Posted with photo: {link}")
            return True, link

        print("sendPhoto failed. Trying sendMessage instead.")
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
        print(f"Posted message: {link}")
        return True, link

    print("sendMessage failed.")
    print(message_response.text[:500])
    return False, link


def main():
    posted_links = load_posted_links()

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
        if link and link not in posted_links:
            new_entries.append(entry)

    if not new_entries:
        print("No new posts found.")
        return

    posts_to_send = new_entries[:MAX_POSTS_PER_RUN]

    for entry in posts_to_send:
        success, link = send_to_telegram(entry)

        if success and link:
            posted_links.add(link)

    save_posted_links(posted_links)


if __name__ == "__main__":
    main()
