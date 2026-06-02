# Facebook + Blogger GitHub Setup Guide — Button by Button

এই guide শুধু আপনার uploaded project-এর জন্য। পুরোনো Telegram system রাখা হয়েছে। নতুন করে Facebook Page এবং Blogger যোগ করা হয়েছে।

---

## 1) ZIP upload/update কোথায় করবেন

### যদি আপনার GitHub repository আগে থেকেই থাকে

1. GitHub খুলুন।
2. আপনার repository খুলুন।
3. `rss_to_telegram.py` ফাইল খুলুন।
4. ডান পাশে/উপরে pencil icon বা **Edit this file** চাপুন।
5. নতুন `rss_to_telegram.py`-এর পুরো code paste করুন।
6. নিচে **Commit changes** চাপুন।
7. `.github/workflows/rss-telegram.yml` ফাইল খুলুন।
8. pencil icon চাপুন।
9. নতুন workflow code paste করুন।
10. **Commit changes** চাপুন।

### যদি নতুন করে পুরো ZIP upload করেন

1. GitHub repository খুলুন।
2. **Add file** চাপুন।
3. **Upload files** চাপুন।
4. ZIP extract করার পর ভিতরের files drag/drop করুন। ZIP file নিজে upload করবেন না।
5. **Commit changes** চাপুন।

---

## 2) GitHub Secrets কোথায় বসাবেন

1. GitHub repository খুলুন।
2. উপরের menu থেকে **Settings** চাপুন।
3. বাম পাশে **Secrets and variables** চাপুন।
4. **Actions** চাপুন।
5. **Secrets** tab select করুন।
6. **New repository secret** চাপুন।
7. `Name` box-এ secret name paste করুন।
8. `Secret` box-এ token/value paste করুন।
9. **Add secret** চাপুন।

---

## 3) Facebook Secrets

একটা একটা করে **New repository secret** চাপবেন।

### Secret 1

Name:

```text
FACEBOOK_PAGE_ID
```

Secret:

```text
আপনার Facebook Page ID paste করুন
```

তারপর **Add secret**।

### Secret 2

Name:

```text
FACEBOOK_PAGE_ACCESS_TOKEN
```

Secret:

```text
আপনার Facebook Page Access Token paste করুন
```

তারপর **Add secret**।

---

## 4) Blogger Secrets

### Secret 1

Name:

```text
BLOGGER_CLIENT_ID
```

Secret:

```text
আপনার Google OAuth Client ID paste করুন
```

তারপর **Add secret**।

### Secret 2

Name:

```text
BLOGGER_CLIENT_SECRET
```

Secret:

```text
আপনার Google OAuth Client Secret paste করুন
```

তারপর **Add secret**।

### Secret 3

Name:

```text
BLOGGER_REFRESH_TOKEN
```

Secret:

```text
আপনার Blogger Refresh Token paste করুন
```

তারপর **Add secret**।

### Secret 4

Name:

```text
BLOGGER_BLOG_ID
```

Secret:

```text
আপনার Blogger Blog ID paste করুন
```

তারপর **Add secret**।

---

## 5) Workflow file-এ কোথায় edit করবেন

File path:

```text
.github/workflows/rss-telegram.yml
```

GitHub-এ:

1. Repository main page খুলুন।
2. `.github` folder খুলুন।
3. `workflows` folder খুলুন।
4. `rss-telegram.yml` খুলুন।
5. pencil icon / **Edit this file** চাপুন।

এই অংশে আপনার WordPress RSS URL বসাবেন:

```yaml
RSS_FEED_URL: "https://varamama.com/listings/feed"
```

আপনার website হলে যেমন:

```yaml
RSS_FEED_URL: "https://your-domain.com/feed/"
```

Facebook এবং Blogger চালু রাখতে:

```yaml
POST_TO_TELEGRAM: "true"
POST_TO_FACEBOOK: "true"
POST_TO_BLOGGER: "true"
```

কোনো platform বন্ধ করতে `true` বদলে `false` লিখবেন।

---

## 6) Workflow manually run করবেন

1. GitHub repository খুলুন।
2. উপরের menu থেকে **Actions** চাপুন।
3. বাম পাশে **WordPress RSS to Telegram Facebook Blogger** চাপুন।
4. ডান পাশে **Run workflow** চাপুন।
5. Branch হিসেবে `main` select করুন।
6. আবার **Run workflow** চাপুন।

---

## 7) Run result কোথায় দেখবেন

1. **Actions** tab খুলুন।
2. সবচেয়ে উপরের/latest run খুলুন।
3. `post-to-social` job খুলুন।
4. red error থাকলে error step খুলুন।

সাধারণ error:

| Error | মানে |
|---|---|
| Facebook is enabled, but ... missing | Facebook secret বসানো হয়নি বা name ভুল |
| Blogger is enabled, but ... missing | Blogger secret বসানো হয়নি বা name ভুল |
| invalid_grant | Blogger refresh token wrong/expired |
| 403 | permission নেই |
| 401 | token invalid/expired |

---

## 8) Copy-paste secret names একসাথে

```text
FACEBOOK_PAGE_ID
FACEBOOK_PAGE_ACCESS_TOKEN
BLOGGER_CLIENT_ID
BLOGGER_CLIENT_SECRET
BLOGGER_REFRESH_TOKEN
BLOGGER_BLOG_ID
```

Telegram আগের মতো থাকলে এগুলোও থাকবে:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

---

## 9) গুরুত্বপূর্ণ সতর্কতা

Token কখনো `rss_to_telegram.py` বা `rss-telegram.yml`-এর ভিতরে directly paste করবেন না। শুধু GitHub Secrets-এ paste করবেন। Workflow file-এ থাকবে শুধু:

```yaml
FACEBOOK_PAGE_ACCESS_TOKEN: ${{ secrets.FACEBOOK_PAGE_ACCESS_TOKEN }}
BLOGGER_REFRESH_TOKEN: ${{ secrets.BLOGGER_REFRESH_TOKEN }}
```
