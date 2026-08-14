# 🕯️ Deaf-ember

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Tweepy](https://img.shields.io/badge/Tweepy-4.16.0-grey?style=for-the-badge&logo=x&logoColor=white&labelColor=000000)
![Facebook Graph API](https://img.shields.io/badge/Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white)
![Instagram Graph API](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)
![X](https://img.shields.io/badge/X-000000?style=for-the-badge&logo=x&logoColor=white)
![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)

A scheduler that automates the annual Deaf-ember art challenge's social media posts across Facebook, Instagram, and X — one prompt a day, all December, wrapping up with a New Year's thank-you post.

📘 [Facebook](https://www.facebook.com/deafember2026) &nbsp;·&nbsp; 📸 [Instagram](https://www.instagram.com/signsoffuncamp/) &nbsp;·&nbsp; 🐦 [X](https://x.com/signsoffuncamp)

## Why
Deaf-ember is a daily art prompt challenge that runs every December for the "Deaf-ember" and "Signs of Fun" communities. Posting the day's prompt, the crossed-off progress graphic, and the right caption by hand across three platforms every single day for a month is tedious and easy to get wrong. This script automates the whole cycle: it runs continuously, checks the date once a day, and — when there's something to post — builds the caption, uploads the right photos, and publishes to every platform, then reports the result to Discord.

## Features
- 📅 Runs on a daily schedule (checks at 12:00 PM local time) and only posts on the days that matter — December 1–31 and January 1st
- ✍️ Auto-generates each day's caption, spelling out the day of the month and pulling that day's prompt from a built-in list
- 📘 Posts to two Facebook Pages (Deaf-ember and Signs of Fun) with the day's focus image and the running crossed-off prompt list
- 📸 Publishes an Instagram carousel by pulling the images straight from the Signs of Fun Facebook post, polling until Meta finishes processing them
- 🐦 Cross-posts the same caption and images to X (Twitter)
- 🔔 Sends a Discord webhook notification for every successful post, with a link to the live post
- 🎉 Automatically wraps the challenge on January 1st with a thank-you post that computes the correct ordinal anniversary year

## Requirements
- Python 3
- Facebook Page admin access for the two target Pages, with an Instagram Business account linked to one of them
- A Meta for Developers app with Graph API access
- A Twitter/X Developer Portal app with Read and Write permissions
- (Optional) A Discord webhook URL for post notifications

## Setup
1. Install dependencies from the repo's root directory:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env-example` to `.env` and fill in the values as described below.

### Facebook & Instagram (Meta)
1. Go to [Meta for Developers](https://developers.facebook.com/apps) and create a new app tied to your Facebook account (any use case that gives you Graph API access works — e.g. "Other" / "Business").
2. Make sure you're an **admin** of the two Facebook Pages you want to post to ("Deaf-ember" and "Signs of Fun"), and that the Instagram account you want to post to is a **Professional (Business/Creator) account** linked to the "Signs of Fun" Page specifically (Instagram app → Settings → Account Center → Linked accounts → Facebook, or from the Page's own Settings → Linked Accounts) — that's the Page this script pulls the Instagram images and posts from.
3. Open the [Graph API Explorer](https://developers.facebook.com/tools/explorer/), select your app, click **Get Access Token**, and grant these permissions: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`. As long as you're an admin/developer/tester on the app, you can generate and use this token yourself without submitting for Meta App Review.
4. This gives you a short-lived User Access Token (good for ~1-2 hours). Exchange it for a long-lived one (~60 days) by calling, from a terminal — never client-side code, since it exposes your App Secret:
   ```
   GET https://graph.facebook.com/v24.0/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id=<YOUR_APP_ID>
     &client_secret=<YOUR_APP_SECRET>
     &fb_exchange_token=<YOUR_SHORT_LIVED_TOKEN>
   ```
   Put the returned token in `META_USER_ACCESS_TOKEN`. It isn't non-expiring — plan to regenerate it roughly every 60 days.
5. Find your two Facebook Page IDs (visible on each Page's About/Page Transparency section, or via `GET /me/accounts` in the Graph API Explorer with your token) and put them in `FB_DEAFEMBER_PAGE_ID` / `FB_SOF_PAGE_ID`.
6. Find your Instagram Business Account ID by querying `GET /<SIGNS_OF_FUN_PAGE_ID>?fields=instagram_business_account` in the Graph API Explorer — the returned `id` goes in `IG_USER_ID`.

### Twitter/X
1. Go to the Twitter Developer Portal.
2. Create a Project and an App (Free tier).
3. Set up User Authentication Settings. Choose "Read and Write" permissions.
4. Go to "Keys and Tokens" and generate your Consumer Keys (API Key/Secret) and Authentication Tokens (Access Token/Secret).

> Ensure to generate and copy tokens _after_ establishing correct (read/write) permissions.

### Discord (optional)
Set `DISCORD_WEBHOOK_URL` to a Discord webhook URL if you want a message posted to a channel every time a post succeeds.

## Usage
Start the script from the repo's root directory:
```bash
python deafember.py
```

As long as the script keeps running, it checks the date every day at 12:00 PM (noon) in the timezone of the machine running it, and posts (or skips) based on the current month/day as described below.

### Updating Prompts and Photos
- The `getPrompt()` function holds the dictionary of prompts, keyed by day of the month — update it for each year's theme.
- The `photos/` folder must contain 63 photos, named `<number>.png` (`1.png`, `2.png`, ... `63.png`), alternating:
  1. A list of all the prompts
  2. Day 1's word
  3. A list of all the prompts with Day 1's word crossed out
  4. Day 2's word
  5. A list of all the prompts with Day 1's and Day 2's words crossed out
  - ...
  63. A list of all the prompts with every word crossed out

## Posts Generated

### December
**Post text**
```
Deaf-ember <year> Day <day of month in words>: The prompt is "<prompt>". Get creative and tag us in your art! Don't forget to use the hashtag #deafember<year>
```
_Example:_ `Deaf-ember 2024 day thirty-one: The prompt is "Abstract". Get creative and tag us in your art! Don't forget to use the hashtag #deafember2024`

**Attachments** — each post carries two photos, in this order:
1. Focused image for today's prompt
2. List of all prompts with previous prompts crossed out

### January 1st
**Post text**
```
That's a wrap! Thank you for participating in our <ordinal>-annual Deaf-ember. Happy New Year! #deafember<year>
```
_Example:_ `That's a wrap! Thank you for participating in our fourth-annual Deaf-ember. Happy New Year! #deafember2024`

**Attachments** — a single photo showing all prompts, fully crossed out.

### Any other day
Nothing happens.

## Project Structure
```
deafember/
├── deafember.py       # Scheduler, content generation, and platform posting logic
├── photos/             # 63 prompt/progress images, named 1.png ... 63.png
├── requirements.txt    # Pinned Python dependencies
├── .env-example        # Template for required API keys/tokens
└── LICENSE
```

## License
MIT — see [LICENSE](LICENSE).
