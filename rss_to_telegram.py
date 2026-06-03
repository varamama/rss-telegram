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
POST_TO_WHATSAPP = os.getenv("POST_TO_WHATSAPP", "false").lower() == "true"
POST_TO_LINKEDIN = os.getenv("POST_TO_LINKEDIN", "false").lower() == "true"
POST_TO_INSTAGRAM = os.getenv("POST_TO_INSTAGRAM", "false").lower() == "true"
POST_TO_PINTEREST = os.getenv("POST_TO_PINTEREST", "false").lower() == "true"
POST_TO_TIKTOK = os.getenv("POST_TO_TIKTOK", "false").lower() == "true"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
FACEBOOK_GRAPH_API_VERSION = os.getenv("FACEBOOK_GRAPH_API_VERSION", "v25.0")

BLOGGER_CLIENT_ID = os.getenv("BLOGGER_CLIENT_ID", "")
BLOGGER_CLIENT_SECRET = os.getenv("BLOGGER_CLIENT_SECRET", "")
BLOGGER_REFRESH_TOKEN = os.getenv("BLOGGER_REFRESH_TOKEN", "")
BLOGGER_BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "")

# WhatsApp Cloud API sends messages to opted-in phone numbers.
# It cannot auto-post to WhatsApp Status or personal/group chats.
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_TO_NUMBERS = [
    n.strip().replace("+", "")
    for n in os.getenv("WHATSAPP_TO_NUMBERS", "").split(",")
    if n.strip()
]
WHATSAPP_GRAPH_API_VERSION = os.getenv("WHATSAPP_GRAPH_API_VERSION", FACEBOOK_GRAPH_API_VERSION)

# LinkedIn author examples:
#   Personal profile: urn:li:person:xxxx
#   Company page:      urn:li:organization:123456
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_AUTHOR_URN = os.getenv("LINKEDIN_AUTHOR_URN", "")
LINKEDIN_API_VERSION = os.getenv("LINKEDIN_API_VERSION", "202605")

# Instagram Graph API requires an Instagram Professional account linked to a Facebook Page.
# Feed image publishing requires a public image URL.
INSTAGRAM_IG_USER_ID = os.getenv("INSTAGRAM_IG_USER_ID", "")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_GRAPH_API_VERSION = os.getenv("INSTAGRAM_GRAPH_API_VERSION", FACEBOOK_GRAPH_API_VERSION)

# Pinterest API v5 creates Pins on a board. It needs a public image URL.
PINTEREST_ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN", "")
PINTEREST_BOARD_ID = os.getenv("PINTEREST_BOARD_ID", "")
PINTEREST_API_BASE_URL = os.getenv("PINTEREST_API_BASE_URL", "https://api.pinterest.com/v5")

# TikTok Content Posting API supports photo/video publishing, not text/link-only posts.
# For PULL_FROM_URL, TikTok requires URLs from a verified domain or URL prefix.
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_REFRESH_TOKEN = os.getenv("TIKTOK_REFRESH_TOKEN", "")
TIKTOK_POST_MODE = os.getenv("TIKTOK_POST_MODE", "DIRECT_POST")  # DIRECT_POST or MEDIA_UPLOAD
TIKTOK_PRIVACY_LEVEL = os.getenv("TIKTOK_PRIVACY_LEVEL", "SELF_ONLY")
TIKTOK_DISABLE_COMMENT = os.getenv("TIKTOK_DISABLE_COMMENT", "false").lower() == "true"
TIKTOK_AUTO_ADD_MUSIC = os.getenv("TIKTOK_AUTO_ADD_MUSIC", "true").lower() == "true"
TIKTOK_BRAND_CONTENT = os.getenv("TIKTOK_BRAND_CONTENT", "false").lower() == "true"
TIKTOK_BRAND_ORGANIC = os.getenv("TIKTOK_BRAND_ORGANIC", "true").lower() == "true"

PLATFORMS = {
    "telegram": POST_TO_TELEGRAM,
    "facebook": POST_TO_FACEBOOK,
    "blogger": POST_TO_BLOGGER,
    "whatsapp": POST_TO_WHATSAPP,
    "linkedin": POST_TO_LINKEDIN,
    "instagram": POST_TO_INSTAGRAM,
    "pinterest": POST_TO_PINTEREST,
    "tiktok": POST_TO_TIKTOK,
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
    require_env(
        POST_TO_WHATSAPP,
        "WhatsApp",
        {
            "WHATSAPP_PHONE_NUMBER_ID": WHATSAPP_PHONE_NUMBER_ID,
            "WHATSAPP_ACCESS_TOKEN": WHATSAPP_ACCESS_TOKEN,
            "WHATSAPP_TO_NUMBERS": WHATSAPP_TO_NUMBERS,
        },
    )
    require_env(
        POST_TO_LINKEDIN,
        "LinkedIn",
        {
            "LINKEDIN_ACCESS_TOKEN": LINKEDIN_ACCESS_TOKEN,
            "LINKEDIN_AUTHOR_URN": LINKEDIN_AUTHOR_URN,
        },
    )
    require_env(
        POST_TO_INSTAGRAM,
        "Instagram",
        {
            "INSTAGRAM_IG_USER_ID": INSTAGRAM_IG_USER_ID,
            "INSTAGRAM_ACCESS_TOKEN": INSTAGRAM_ACCESS_TOKEN,
        },
    )
    require_env(
        POST_TO_PINTEREST,
        "Pinterest",
        {
            "PINTEREST_ACCESS_TOKEN": PINTEREST_ACCESS_TOKEN,
            "PINTEREST_BOARD_ID": PINTEREST_BOARD_ID,
        },
    )
    if POST_TO_TIKTOK and not (
        TIKTOK_ACCESS_TOKEN
        or (TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET and TIKTOK_REFRESH_TOKEN)
    ):
        raise ConfigError(
            "TikTok is enabled, but missing TIKTOK_ACCESS_TOKEN or the refresh-token set: "
            "TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REFRESH_TOKEN."
        )

    if POST_TO_TIKTOK and TIKTOK_POST_MODE not in {"DIRECT_POST", "MEDIA_UPLOAD"}:
        raise ConfigError("TIKTOK_POST_MODE must be DIRECT_POST or MEDIA_UPLOAD.")


def empty_status():
    return {name: False for name in PLATFORMS}


def load_posted_state():
    """Load posting state.

    Backward compatibility:
    - Old file format was a list of links already posted to Telegram.
    - New format is a dict: {link: {"telegram": true, "facebook": true, ...}}
    """
    if not STATE_FILE.exists():
        return {}

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if isinstance(data, list):
        return {str(link): {**empty_status(), "telegram": True} for link in data if link}

    if isinstance(data, dict):
        normalized = {}
        for link, status in data.items():
            if isinstance(status, dict):
                base = empty_status()
                for name in PLATFORMS:
                    base[name] = bool(status.get(name, False))
                normalized[str(link)] = base
            elif isinstance(status, list):
                normalized[str(link)] = {name: name in status for name in PLATFORMS}
            elif isinstance(status, bool):
                normalized[str(link)] = {name: bool(status) for name in PLATFORMS}
        return normalized

    return {}


def save_posted_state(posted_state):
    ordered = {}
    for link, status in sorted(posted_state.items()):
        base = empty_status()
        if isinstance(status, dict):
            for name in PLATFORMS:
                base[name] = bool(status.get(name, False))
        ordered[link] = base

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


def get_video_url(entry):
    """Return a public video URL from RSS media/enclosure fields, if present."""
    for media_item in entry.get("media_content", []):
        url = media_item.get("url")
        media_type = media_item.get("type", "")
        medium = media_item.get("medium", "")
        if url and (media_type.startswith("video/") or medium == "video"):
            return url

    for enclosure in entry.get("enclosures", []):
        href = enclosure.get("href") or enclosure.get("url")
        enc_type = enclosure.get("type", "")
        if href and enc_type.startswith("video/"):
            return href

    for link_item in entry.get("links", []):
        href = link_item.get("href")
        link_type = link_item.get("type", "")
        rel = link_item.get("rel", "")
        if href and (link_type.startswith("video/") or (rel == "enclosure" and ".mp4" in href.lower())):
            return href

    return None


def clamp_text(value, max_chars):
    value = str(value or "").strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."


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


def build_social_text(entry, link, max_summary_chars=350):
    title = entry.get("title", "নতুন লিস্টিং")
    summary = get_summary_text(entry, max_chars=max_summary_chars)

    parts = [f"🏠 নতুন লিস্টিং\n\n{title}"]
    if summary:
        parts.append(summary)
    parts.append(f"বিস্তারিত দেখুন: {link}")
    return "\n\n".join(parts)


def build_facebook_message(entry, link):
    return build_social_text(entry, link, max_summary_chars=350)


def build_whatsapp_message(entry, link):
    return build_social_text(entry, link, max_summary_chars=600)


def build_linkedin_message(entry, link):
    return build_social_text(entry, link, max_summary_chars=600)


def build_instagram_caption(entry, link):
    # Instagram captions can contain URLs, but they are not clickable in normal feed captions.
    return build_social_text(entry, link, max_summary_chars=900)


def build_pinterest_description(entry, link):
    return clamp_text(build_social_text(entry, link, max_summary_chars=400), 500)


def build_tiktok_title(entry):
    return clamp_text(entry.get("title", "নতুন লিস্টিং"), 90)


def build_tiktok_description(entry, link):
    return clamp_text(build_social_text(entry, link, max_summary_chars=900), 2200)


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


def send_to_whatsapp(entry, link):
    message = build_whatsapp_message(entry, link)
    url = f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    all_ok = True
    for number in WHATSAPP_TO_NUMBERS:
        response = requests.post(
            url,
            headers=headers,
            json={
                "messaging_product": "whatsapp",
                "to": number,
                "type": "text",
                "text": {
                    "preview_url": True,
                    "body": message,
                },
            },
            timeout=30,
        )

        if response.ok:
            data = response.json()
            print(f"WhatsApp sent to {number}: {link} | message id: {data.get('messages', [{}])[0].get('id')}")
        else:
            all_ok = False
            print(f"WhatsApp send failed for {number}.")
            print(response.text[:1000])

    return all_ok


def send_to_linkedin(entry, link):
    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "LinkedIn-Version": LINKEDIN_API_VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author": LINKEDIN_AUTHOR_URN,
        "commentary": build_linkedin_message(entry, link),
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)

    if response.status_code in (200, 201):
        print(f"LinkedIn posted: {link} | post id: {response.headers.get('x-restli-id', '')}")
        return True

    print("LinkedIn post failed.")
    print(response.text[:1000])
    return False


def send_to_instagram(entry, link):
    image_url = get_image_url(entry)
    if not image_url:
        print("Instagram skipped: no public image URL found in RSS entry. Instagram feed publishing needs an image.")
        return False

    caption = build_instagram_caption(entry, link)
    media_url = f"https://graph.facebook.com/{INSTAGRAM_GRAPH_API_VERSION}/{INSTAGRAM_IG_USER_ID}/media"
    publish_url = f"https://graph.facebook.com/{INSTAGRAM_GRAPH_API_VERSION}/{INSTAGRAM_IG_USER_ID}/media_publish"

    media_response = requests.post(
        media_url,
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=60,
    )

    if not media_response.ok:
        print("Instagram media container creation failed.")
        print(media_response.text[:1000])
        return False

    creation_id = media_response.json().get("id")
    if not creation_id:
        print("Instagram media container creation failed: missing creation id.")
        print(media_response.text[:1000])
        return False

    publish_response = requests.post(
        publish_url,
        data={
            "creation_id": creation_id,
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=60,
    )

    if publish_response.ok:
        data = publish_response.json()
        print(f"Instagram posted: {link} | media id: {data.get('id')}")
        return True

    print("Instagram publish failed.")
    print(publish_response.text[:1000])
    return False


def send_to_pinterest(entry, link):
    image_url = get_image_url(entry)
    if not image_url:
        print("Pinterest skipped: no public image URL found in RSS entry. Pinterest Pin creation needs an image URL.")
        return False

    url = f"{PINTEREST_API_BASE_URL.rstrip('/')}/pins"
    headers = {
        "Authorization": f"Bearer {PINTEREST_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "board_id": PINTEREST_BOARD_ID,
        "title": clamp_text(entry.get("title", "নতুন লিস্টিং"), 100),
        "description": build_pinterest_description(entry, link),
        "link": link,
        "media_source": {
            "source_type": "image_url",
            "url": image_url,
        },
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)

    if response.status_code in (200, 201):
        data = response.json()
        print(f"Pinterest Pin created: {link} | pin id: {data.get('id')}")
        return True

    print("Pinterest Pin creation failed.")
    print(response.text[:1000])
    return False


def get_tiktok_access_token():
    if TIKTOK_ACCESS_TOKEN:
        return TIKTOK_ACCESS_TOKEN

    response = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": TIKTOK_CLIENT_KEY,
            "client_secret": TIKTOK_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": TIKTOK_REFRESH_TOKEN,
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(f"TikTok token refresh failed: {response.text[:1000]}")

    data = response.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"TikTok token refresh response did not include access_token: {response.text[:1000]}")

    if data.get("refresh_token") and data.get("refresh_token") != TIKTOK_REFRESH_TOKEN:
        print("TikTok returned a new refresh_token. Update GitHub Secret TIKTOK_REFRESH_TOKEN with the new value.")

    return token


def send_to_tiktok(entry, link):
    video_url = get_video_url(entry)
    image_url = get_image_url(entry)
    access_token = get_tiktok_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    # Prefer video if the RSS item has a video enclosure. Otherwise use photo mode.
    if video_url:
        url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
        payload = {
            "post_info": {
                "privacy_level": TIKTOK_PRIVACY_LEVEL,
                "title": build_tiktok_description(entry, link),
                "disable_comment": TIKTOK_DISABLE_COMMENT,
                "disable_duet": False,
                "disable_stitch": False,
                "brand_content_toggle": TIKTOK_BRAND_CONTENT,
                "brand_organic_toggle": TIKTOK_BRAND_ORGANIC,
                "is_aigc": False,
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "video_url": video_url,
            },
        }
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    elif image_url:
        url = "https://open.tiktokapis.com/v2/post/publish/content/init/"
        post_info = {
            "title": build_tiktok_title(entry),
            "description": build_tiktok_description(entry, link),
        }
        if TIKTOK_POST_MODE == "DIRECT_POST":
            post_info.update(
                {
                    "privacy_level": TIKTOK_PRIVACY_LEVEL,
                    "disable_comment": TIKTOK_DISABLE_COMMENT,
                    "auto_add_music": TIKTOK_AUTO_ADD_MUSIC,
                    "brand_content_toggle": TIKTOK_BRAND_CONTENT,
                    "brand_organic_toggle": TIKTOK_BRAND_ORGANIC,
                }
            )

        payload = {
            "post_info": post_info,
            "source_info": {
                "source": "PULL_FROM_URL",
                "photo_cover_index": 0,
                "photo_images": [image_url],
            },
            "post_mode": TIKTOK_POST_MODE,
            "media_type": "PHOTO",
        }
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    else:
        print("TikTok skipped: no public image/video URL found. TikTok Content Posting API needs photo or video media.")
        return False

    if response.ok:
        data = response.json()
        error = data.get("error", {})
        if error.get("code") in (None, "ok"):
            print(f"TikTok initialized: {link} | publish id: {data.get('data', {}).get('publish_id')}")
            return True

    print("TikTok post initialization failed.")
    print(response.text[:1000])
    return False


def platform_needs_post(posted_state, link, platform):
    if not PLATFORMS.get(platform):
        return False
    return not posted_state.get(link, {}).get(platform, False)


def entry_needs_any_enabled_platform(posted_state, link):
    return any(platform_needs_post(posted_state, link, platform) for platform in PLATFORMS)


def post_entry_to_enabled_platforms(entry, link, posted_state):
    posted_state.setdefault(link, empty_status())

    if platform_needs_post(posted_state, link, "telegram"):
        posted_state[link]["telegram"] = send_to_telegram(entry, link)

    if platform_needs_post(posted_state, link, "facebook"):
        posted_state[link]["facebook"] = send_to_facebook(entry, link)

    if platform_needs_post(posted_state, link, "blogger"):
        posted_state[link]["blogger"] = send_to_blogger(entry, link)

    if platform_needs_post(posted_state, link, "whatsapp"):
        posted_state[link]["whatsapp"] = send_to_whatsapp(entry, link)

    if platform_needs_post(posted_state, link, "linkedin"):
        posted_state[link]["linkedin"] = send_to_linkedin(entry, link)

    if platform_needs_post(posted_state, link, "instagram"):
        posted_state[link]["instagram"] = send_to_instagram(entry, link)

    if platform_needs_post(posted_state, link, "pinterest"):
        posted_state[link]["pinterest"] = send_to_pinterest(entry, link)

    if platform_needs_post(posted_state, link, "tiktok"):
        posted_state[link]["tiktok"] = send_to_tiktok(entry, link)

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
