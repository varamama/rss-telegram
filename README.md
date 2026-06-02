# WordPress RSS to Telegram + Facebook Page + Blogger Auto Poster

এই repository WordPress RSS feed থেকে নতুন post নিয়ে Telegram, Facebook Page এবং Blogger-এ auto post করে।

## Files

- `rss_to_telegram.py` — main script. নাম পুরোনো রাখা হয়েছে, কিন্তু এখন Telegram + Facebook + Blogger support করে।
- `.github/workflows/rss-telegram.yml` — GitHub Actions workflow.
- `posted_links.json` — কোন link কোন platform-এ post হয়েছে সেটার record.
- `requirements.txt` — Python dependencies.
- `SETUP_GUIDE_BN.md` — বাংলায় full setup guide.

## Required GitHub Secrets

### Telegram

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### Facebook Page

- `FACEBOOK_PAGE_ID`
- `FACEBOOK_PAGE_ACCESS_TOKEN`

### Blogger

- `BLOGGER_CLIENT_ID`
- `BLOGGER_CLIENT_SECRET`
- `BLOGGER_REFRESH_TOKEN`
- `BLOGGER_BLOG_ID`

## Enable/disable platform

Open `.github/workflows/rss-telegram.yml` and edit:

```yaml
POST_TO_TELEGRAM: "true"
POST_TO_FACEBOOK: "true"
POST_TO_BLOGGER: "true"
```

`true` = চালু, `false` = বন্ধ।

## Run manually

GitHub repo → Actions → WordPress RSS to Telegram Facebook Blogger → Run workflow.
