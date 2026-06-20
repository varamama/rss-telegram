# WordPress RSS to Multi Social Auto Poster

এই project WordPress RSS feed থেকে নতুন listing/post নিয়ে Telegram, Facebook, Blogger, WhatsApp, LinkedIn, Instagram, Pinterest এবং TikTok-এ auto post করার জন্য তৈরি।

সব platform-এ মূল post format এখন এক রকম:

```text
Title

Description

ওয়েবসাইট লিংক:
https://varamama.com/post-link
```

## এই fixed version-এ যা ঠিক করা হয়েছে

- LinkedIn-এ ভুল `| Vara Mama` / শুধু website name post হওয়া বন্ধ করা হয়েছে।
- RSS title ভুল হলে listing page থেকে `og:title`, `h1`, page title এবং URL slug দিয়ে title ঠিক করা হবে।
- Description না থাকলে page metadata থেকে description নেওয়া হবে। সেটিও না থাকলে clean fallback text ব্যবহার করবে।
- LinkedIn এখন default ভাবে **media-first** post করবে: আগে image upload, তারপর exact text + uploaded image. এতে broken link-preview/photo error কমে।
- LinkedIn article/card mode optional রাখা হয়েছে: `LINKEDIN_POST_STYLE: "article"` দিলে চালু হবে। Default `media` রাখা নিরাপদ।
- Broken/placeholder/too-small image detect করে skip করা হয়, তাই social media-তে photo error image দেখানোর সম্ভাবনা কমে।
- Facebook valid image পেলে photo post করবে; image invalid হলে normal link/text post করবে।
- Telegram photo fail করলে automatic text fallback করবে।
- RSS-এ image না থাকলে listing page থেকে `og:image`, `twitter:image`, WordPress featured image খুঁজবে।
- Manual repost option আছে: GitHub Actions run করার সময় `force_repost_platforms` box-এ `linkedin` লিখলে LinkedIn corrected format-এ আবার post করবে।

## Files

- `rss_to_telegram.py` — main Python script.
- `.github/workflows/rss-telegram.yml` — GitHub Actions workflow.
- `posted_links.json` — কোন link কোন platform-এ already posted হয়েছে তার record.
- `requirements.txt` — Python dependencies.
- `SETUP_GUIDE_BN.md` — বাংলায় setup guide.

## Required GitHub Secrets

### Telegram

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

### Facebook Page

```text
FACEBOOK_PAGE_ID
FACEBOOK_PAGE_ACCESS_TOKEN
```

### Blogger

```text
BLOGGER_CLIENT_ID
BLOGGER_CLIENT_SECRET
BLOGGER_REFRESH_TOKEN
BLOGGER_BLOG_ID
```

### LinkedIn

```text
LINKEDIN_ACCESS_TOKEN
LINKEDIN_AUTHOR_URN
```

LinkedIn author URN examples:

```text
Personal profile: urn:li:person:xxxx
Company page:      urn:li:organization:123456
```

## LinkedIn post style

Default safe setting:

```yaml
LINKEDIN_POST_STYLE: "media"
```

এতে LinkedIn-এ post হবে exact text + uploaded image হিসেবে। Website preview card না বানানোর কারণে `| Vara Mama` বা broken photo preview আসবে না।

Article/card চাইলে:

```yaml
LINKEDIN_POST_STYLE: "article"
```

কিন্তু website metadata ভুল থাকলে article card আবার ভুল দেখাতে পারে, তাই default `media` রাখাই ভালো।

## Manual repost for corrected LinkedIn posts

আগের ভুল LinkedIn posts corrected format-এ repost করতে:

1. GitHub repo → **Actions**
2. **WordPress RSS to Multi Social Auto Poster** workflow খুলুন
3. **Run workflow** চাপুন
4. `force_repost_platforms` box-এ লিখুন:

```text
linkedin
```

5. Run করুন।

## Important note

`posted_links.json` delete করলে সব enabled platforms পুরোনো RSS posts আবার post করতে পারে। শুধুমাত্র LinkedIn repost দরকার হলে manual input `linkedin` ব্যবহার করুন।
