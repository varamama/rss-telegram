# RSS Social Auto Poster — Bangla Setup Guide

এই guide updated/fixed auto poster project-এর জন্য। এখন সব post clean format-এ যাবে:

```text
Title

Description

ওয়েবসাইট লিংক:
https://varamama.com
```

---

## 1) GitHub repository-তে updated files upload/replace করুন

### Existing repository থাকলে

1. ZIP extract করুন।
2. GitHub repository খুলুন।
3. নিচের files replace করুন:
   - `rss_to_telegram.py`
   - `.github/workflows/rss-telegram.yml`
   - `requirements.txt`
   - `README.md`
   - `SETUP_GUIDE_BN.md`
4. **Commit changes** চাপুন।

### নতুন repository হলে

1. ZIP extract করুন।
2. GitHub repository খুলুন।
3. **Add file → Upload files** চাপুন।
4. ZIP file upload করবেন না; ZIP extract করার পর ভিতরের files upload করুন।
5. **Commit changes** চাপুন।

---

## 2) GitHub Secrets বসানোর নিয়ম

1. GitHub repository খুলুন।
2. **Settings** চাপুন।
3. বাম পাশে **Secrets and variables → Actions** চাপুন।
4. **New repository secret** চাপুন।
5. Secret name এবং value বসিয়ে **Add secret** চাপুন।

---

## 3) Required secrets

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

`LINKEDIN_AUTHOR_URN` উদাহরণ:

```text
Personal profile: urn:li:person:xxxx
Company page:      urn:li:organization:123456
```

LinkedIn permission:

- Personal profile posting: usually `w_member_social`
- Company page posting: page admin access + organization posting permission/token দরকার

Token/secret কখনো public chat বা GitHub code file-এ লিখবেন না। শুধু GitHub Secrets-এ রাখবেন।

---

## 4) LinkedIn ভুল post/photo error সমাধানের জন্য গুরুত্বপূর্ণ setting

Workflow file `.github/workflows/rss-telegram.yml`-এ এই line রাখা হয়েছে:

```yaml
LINKEDIN_POST_STYLE: "media"
```

এটাই safe mode। এই mode-এ:

- LinkedIn আগে image upload করে
- তারপর exact text + uploaded image দিয়ে post করে
- Website preview/card generate করে না
- তাই `| Vara Mama`, শুধু website name, বা broken photo preview দেখানোর chance কমে যায়

যদি আপনি LinkedIn website card চান, তখন only তখন:

```yaml
LINKEDIN_POST_STYLE: "article"
```

কিন্তু আপনার screenshot-এর মতো ভুল format আসার কারণ সাধারণত website/RSS metadata ভুল হওয়া। তাই `media` রাখাই recommended।

---

## 5) Workflow run করবেন যেভাবে

1. GitHub repo → **Actions**
2. **WordPress RSS to Multi Social Auto Poster** খুলুন।
3. **Run workflow** চাপুন।
4. সাধারণ run করতে input blank রাখুন।
5. **Run workflow** চাপুন।

Workflow প্রতি 15 মিনিটে auto run হবে।

---

## 6) আগের ভুল LinkedIn post corrected format-এ repost করতে

পুরো `posted_links.json` delete করবেন না; এতে সব platform-এ duplicate post হতে পারে। শুধু LinkedIn repost করতে:

1. GitHub repo → **Actions**
2. Workflow খুলুন।
3. **Run workflow** চাপুন।
4. `force_repost_platforms` field-এ লিখুন:

```text
linkedin
```

5. Run করুন।

একাধিক platform repost করতে চাইলে:

```text
linkedin,facebook
```

---

## 7) Error হলে কোথায় দেখবেন

1. GitHub repo → **Actions**
2. Failed workflow run খুলুন
3. **Run RSS social auto poster** step খুলুন
4. Error message দেখুন

Common error:

### LinkedIn 401/403

কারণ: token expired, permission নেই, wrong author URN, company page admin access নেই।

সমাধান: নতুন LinkedIn access token generate করে GitHub Secret update করুন। Company page হলে page admin permission নিশ্চিত করুন।

### LinkedIn image upload failed

কারণ: image URL private/broken/too small/unsupported format অথবা LinkedIn permission issue।

সমাধান: script এখন image fail হলে text-only fallback করবে। ভালো result চাইলে website post/listing-এ public JPG/PNG featured image দিন।

### Facebook photo failed

কারণ: invalid image URL বা Page token permission issue।

সমাধান: script photo fail হলে feed/link fallback করবে। Token permission ঠিক করুন।

### Instagram skipped

কারণ: Instagram feed publish করতে public image URL দরকার। RSS/listing image না থাকলে Instagram skip করবে।

---

## 8) Website side-এ ঠিক রাখবেন

প্রতিটি listing/post page-এ এগুলো থাকলে social post বেশি সুন্দর হবে:

```html
<meta property="og:title" content="Post title">
<meta property="og:description" content="Post description">
<meta property="og:image" content="https://your-site.com/image.jpg">
```

WordPress হলে প্রতিটি post/listing-এ Featured Image দিন। Image public হতে হবে এবং JPG/PNG হলে ভালো।
