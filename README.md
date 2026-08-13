# Install Required Libraries 
In the repo's root directory, run the following command: 
`pip install -r requirements.txt`

# Setup Needed Keys
Using the .env-example file as a guide, create an .env file and fill in the values as follows:
## Facebook & Instagram (Meta)
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

## Twitter/X
1. Go to the Twitter Developer Portal
2. Create a Project and an App (Free tier)
3. Set up User Authentication Settings. Choose "Read and Write" permissions.
4. Go to "Keys and Tokens" and generate your Consumer Keys (API Key/Secret) and Authentication Tokens (Access Token/Secret).

> Ensure to generate and copy tokens _after_ establishing correct (read/write) permissions

# Updating Prompts and Photos
The `getPrompt()` method should be updated to have a dictionary of the prompts, keyed by the day of the month. The photos/ folder should include 63 photos in the following format:
1. A list of all the prompts 
2. Day 1's Word
3. A list of all the prompts with Day 1's Word crossed out
4. Day 2's Word
5. A list of all the prompts with Day 1's and Day 2's Words crossed out
...
63\. A list of all the prompts with all Words crossed out

Each photo should be named `<number>.png` (1.png, 2.png, etc.).

# Running the File
You can begin the script with the following command in the repo's root directory: 
`python deafember.py`

As long as the script is running, the function will be called every day at 12:00 PM (Noon) in the timezone of the machine running the script. Based on the current month/day, posts will be generated (or skipped) as outlined below. 

# Posts Generated

## December
### Post Text
Deaf-ember `<year>` Day `<day of month in words>`: The prompt is "`<prompt>`". Get creative and tag us in your art! Don't forget to use the hashtag #deafember`<year>`

**_Example_**
Deaf-ember 2024 day thirty-one: The prompt is "Abstract". Get creative and tag us in your art! Don't forget to use the hashtag #deafember2024

### Post Attachments
Each post contains two photos, in the following order - 
1. Focused image for today's prompt
2. List of all prompts with previous prompts crossed out

## January 1st
### Post Text
That's a wrap! Thank you for participating in our `<appropriate ordinal number>`-annual Deaf-ember. Happy New Year! #deafember`<year>`

**_Example_**
That's a wrap! Thank you for participating in our fourth-annual Deaf-ember. Happy New Year! #deafember2024

### Post Attachments
A single photo of all prompts, all crossed out is attached to the post. 

## Other Days (Not December/January 1st)
Nothing Happens