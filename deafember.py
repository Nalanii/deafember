import requests
import json
import tweepy
import os
from dotenv import dotenv_values
import datetime
from num2words import num2words
import schedule
import time

# ==============================================================================
# CONFIGURATION
# ==============================================================================

config = dotenv_values(".env")

class PostContent:
    def __init__(self, message, attachments=[]):
        self.message = message
        self.attachments = attachments

BASE_FB_URL = "https://graph.facebook.com/v24.0"

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def log_result(ok: bool, ok_msg: str, fail_msg: str):
    print(ok_msg if ok else fail_msg)

def require(value, message):
    if not value:
        print(f"⚠️ {message}")
        return None
    return value

def send_discord_message(content):
    webhook_url = config.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("⚠️ Discord Webhook URL not set in config.")
        return
    
    print("Sending Discord message...", end="")

    payload = {
        "content": content
    }
    response = requests.post(webhook_url, json=payload)
    ok = response.status_code == 204
    log_result(ok, "✅ Success.", f"❌ Failed: {response.status_code} - {response.text}")

def upload_unpublished_photo_on_facebook(access_token, image_source):
    print('\t↳ Uploading Unpublished Photo to Facebook...', end="")
    url = f"{BASE_FB_URL}/me/photos"
    
    payload = {
        'access_token': access_token,
        'published': 'false'
    }
       
    if not os.path.exists(image_source):
        print(f'❌ Failed: File not found at {image_source}')
        return None

    try:
        # Note: 'files' is handled automatically by requests as multipart/form-data
        with open(image_source, 'rb') as f:
            files = {'source': f}
            response = requests.post(url, data=payload, files=files)
            data = response.json()

        ok = 'id' in data
        log_result(ok, f"✅ Success. Photo ID: {data.get('id')}", f'❌ Failed: {data}')
        return data.get('id') if ok else None
    except Exception as e:
        print(f'❌ Failed: {e}')
        return None

def get_facebook_access_tokens():
    print('Fetching Facebook Access Tokens...', end="")
    url = f"{BASE_FB_URL}/me/accounts"
    payload = {
        'access_token': config.get('META_USER_ACCESS_TOKEN')
    }
    r = requests.get(url, params=payload)
    data = r.json()
    ok = r.status_code == 200
    log_result(ok, "✅ Success", f'❌ Failed: {r.text}')
    return data if ok else []
    
def get_page_token(data, target_id):
    for page in data.get('data', []):
        if page.get('id') == target_id:
            return page.get('access_token')
    return None # Return None if the ID isn't found

def get_image_urls_from_facebook_post(access_token, post_id):
    print('Extracting Image URLs from Facebook Post...', end="")
    url = f"{BASE_FB_URL}/{post_id}"
    params = {
        'fields': 'attachments{subattachments.limit(10){media{image{src}}}}',
        'access_token': access_token
    }
    
    r = requests.get(url, params=params)
    data = r.json()
    
    image_urls = []
    
    try:
        attachments = data.get('attachments', {}).get('data', [])
        if attachments:
            sub_attachments = attachments[0].get('subattachments', {}).get('data', [])
            
            for item in sub_attachments:
                src = item.get('media', {}).get('image', {}).get('src')
                if src:
                    image_urls.append(src)
                    
    except Exception as e:
        print(f"❌ Failed. Could not extract URLs: {e}")
    
    print('✅ Success. Found', len(image_urls), 'image URLs.')

    return image_urls

# ==============================================================================
# PLATFORM POSTING FUNCTIONS
# ==============================================================================

def post_to_facebook_page(access_token: str, group_or_page_id: str, post_content: PostContent):
    print(f'Posting to Facebook Page ({group_or_page_id}):')
    url = f"{BASE_FB_URL}/{group_or_page_id}/feed"
   
    attached_media = []
    for attachment in post_content.attachments:
        photo_id = upload_unpublished_photo_on_facebook(access_token, attachment)
        if photo_id:
            # Format required by Graph API: [{"media_fbid": "123"}, ...]
            attached_media.append({"media_fbid": photo_id})

    payload = {
        'message': post_content.message,
        'attached_media': json.dumps(attached_media),
        'access_token': access_token,
        'fields': ['permalink_url']
    }
    print('\t↳ Publishing to Facebook...', end="")

    r = requests.post(url, data=payload)
    data = r.json()

    ok = r.status_code == 200
    post_url = data.get('permalink_url')
    log_result(ok, f"✅ Success. URL: {post_url}", f"❌ Failed: {r.text}")
    if ok:
        send_discord_message(f"New Facebook Post Created: {post_url}")
    
    return data.get('id') # Post ID

def post_instagram_carousel(access_token: str, ig_user_id: str, image_urls: list, caption: str):
    print('Posting to Instagram:')
    # --- PHASE 1a: Create Individual Item Containers (all at once) ---
    pending_container_ids = []

    for url in image_urls:
        print(f"\t↳ Creating item for image URL...", end="")
        url_create = f"{BASE_FB_URL}/{ig_user_id}/media"
        payload = {
            'image_url': url,
            'is_carousel_item': 'true',  # CRITICAL: Marks this as a child item
            'access_token': access_token
        }

        r = requests.post(url_create, data=payload)
        data = r.json()

        if 'id' in data:
            print(f"✅ Container created. ID: {data['id']}")
            pending_container_ids.append(data['id'])
        else:
            print(f"❌ Failed: {data}")
            return

    # --- PHASE 1b: Poll all pending containers together for FINISHED status ---
    MAX_RETRIES = 10
    DELAY = 5  # seconds
    media_payload = {
        'fields': 'status_code',
        'access_token': access_token
    }
    item_container_ids = []

    for attempt in range(MAX_RETRIES):
        still_pending = []

        for container_id in pending_container_ids:
            media_url = f"{BASE_FB_URL}/{container_id}"
            media_response = requests.get(media_url, params=media_payload)
            media_data = media_response.json()
            status = media_data.get('status_code')

            if status == 'FINISHED':
                print(f"\t↳ ✅ Container {container_id} finished processing.")
                item_container_ids.append(container_id)
            elif status == 'ERROR':
                print(f"❌ Failed: Media processing failed for container {container_id}.")
                return
            else:
                still_pending.append(container_id)

        pending_container_ids = still_pending

        if not pending_container_ids:
            break

        print(f"\t↳ Processing (Attempt {attempt + 1}/{MAX_RETRIES}): "
              f"{len(pending_container_ids)} container(s) still pending...")
        time.sleep(DELAY)

    if pending_container_ids:
        print("❌ Failed: Timed out waiting for media processing.")
        return

    if not item_container_ids:
        print("❌ No items were successfully created.")
        return

    # --- PHASE 2: Create the Carousel (Parent) Container ---
    print("\t↳ Creating Parent Container...", end="")
    
    url_carousel = f"{BASE_FB_URL}/{ig_user_id}/media"
    payload = {
        'media_type': 'CAROUSEL',
        'caption': caption,
        'children': ','.join(item_container_ids), # List of IDs as CSV string
        'access_token': access_token
    }
    
    r = requests.post(url_carousel, data=payload)
    carousel_result = r.json()
    
    ok = 'id' in carousel_result
    log_result(ok, f"✅ Success. ID: {carousel_result.get('id')}", f"❌ Failed: {carousel_result}")
    if not ok:
        return

    creation_id = carousel_result['id']

    # --- PHASE 3: Publish the Carousel ---
    print("\t↳ Publishing to Instagram...", end="")
    
    url_publish = f"{BASE_FB_URL}/{ig_user_id}/media_publish"
    publish_payload = {
        'creation_id': creation_id,
        'access_token': access_token
    }
    
    r_publish = requests.post(url_publish, data=publish_payload)
    publish_result = r_publish.json()

    if 'id' in publish_result:
        media_id = publish_result['id']
        url_url = f"{BASE_FB_URL}/{media_id}"
        url_payload = {
            'fields': 'permalink',
            'access_token': access_token
        }
        r_url = requests.get(url_url, params=url_payload)
        url_data = r_url.json()
        post_url = url_data.get('permalink')
        print(f"✅ Success. URL: {post_url}")
        send_discord_message(f"✅ New Instagram Post Created: {post_url}")
    else:
        print(f"❌ Failed: {publish_result}")

def post_to_twitter(post_content: PostContent):
    print("Posting to Twitter...", end="")
    client = tweepy.Client(
        consumer_key=config.get('TWITTER_API_KEY'),
        consumer_secret=config.get('TWITTER_API_SECRET'),
        access_token=config.get('TWITTER_ACCESS_TOKEN'),
        access_token_secret=config.get('TWITTER_ACCESS_SECRET'),
    )
    
    # Authenticate v1.1 for media upload (v2 doesn't support media upload yet easily)
    auth = tweepy.OAuth1UserHandler(
        config.get('TWITTER_API_KEY'), config.get('TWITTER_API_SECRET'),
        config.get('TWITTER_ACCESS_TOKEN'), config.get('TWITTER_ACCESS_SECRET')
    )
    api = tweepy.API(auth)

    try:
        # Upload image
        media_ids = []
        for filename in post_content.attachments:
            # Uploads to v1.1 endpoint
            res = api.media_upload(filename)
            media_ids.append(res.media_id)
        # Create Tweet
        response = client.create_tweet(text=post_content.message, media_ids=media_ids)
        post_url = f"https://x.com/user/status/{response.data['id']}"
        print(f"✅ Success. URL: {post_url}")
        send_discord_message(f"✅ New Twitter Post Created: {post_url}")

    except Exception as e:
        print(f"❌ Failed: {e}")

# ==============================================================================
# CONTENT FUNCTIONS
# ==============================================================================

def getPrompt(day_of_month):
    prompts = {
        1: "Spark",
        2: "Hands",
        3: "Silence",
        4: "Proud",
        5: "Story",
        6: "Visual",
        7: "Echo",
        8: "Identity",
        9: "Bold",
        10: "Unseen",
        11: "Movement",
        12: "Roots",
        13: "Deaf",
        14: "Glow",
        15: "Language",
        16: "Barrier",
        17: "Believe",
        18: "Access",
        19: "Family",
        20: "Culture",
        21: "Community",
        22: "Power",
        23: "Journey",
        24: "Resist",
        25: "Gesture",
        26: "Connection",
        27: "Fire",
        28: "Joy",
        29: "Pioneer",
        30: "Me",
        31: "Ember"
    }
    if prompts.get(day_of_month) is None:
        raise ValueError("Invalid day of month for prompt.")
    return prompts.get(day_of_month)

def getText(day_of_month, year):
    return f"Deaf-ember {year} Day {num2words(day_of_month)}: The prompt is \"{getPrompt(day_of_month)}\". Get creative and tag us in your art! Don't forget to use the hashtag #deafember{year}"

def december_post(today):
    current_day_of_month = today.day
    main_photo_path = f"./photos/{(current_day_of_month*2)}.png"
    print(f"Using main photo path: {main_photo_path}")
    list_photo_path = f"./photos/{((current_day_of_month*2)-1)}.png"
    print(f"Using list photo path: {list_photo_path}")

    text = getText(current_day_of_month, today.year)
    print(f"Generated text: {text}")

    return PostContent(
        message=text,
        attachments=[main_photo_path, list_photo_path]
    )

def january_post(today):
    FIRST_DEAFEMBER_YEAR = 2021
    last_year = today.year - 1
    annual_count = last_year - FIRST_DEAFEMBER_YEAR + 1

    return PostContent(
        message=f"That's a wrap! Thank you for participating in our {num2words(annual_count, to='ordinal')}-annual Deaf-ember. Happy New Year! #deafember{last_year}",
        attachments=["./photos/63.png"]
    )

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def check_date_and_run():
    today = datetime.date.today()

    content = None

    # Check if today is in December
    if today.month == 12:
        print("--- Content ---")
        content = december_post(today)
        
    # Check if today is January 1st (Month 1, Day 1)
    elif today.month == 1 and today.day == 1:
        print("--- Content ---")
        content = january_post(today)
        
    # Otherwise do nothing
    else:
        print("No scheduled posts for today.")
        return
    
    print("\n--- Setup ---")
    
    deafember_page_id = require(config.get('FB_DEAFEMBER_PAGE_ID'), "Deafember Page ID not set in config.")
    if not deafember_page_id:
        return

    signs_of_fun_page_id = require(config.get('FB_SOF_PAGE_ID'), "Signs of Fun Page ID not set in config.")
    if not signs_of_fun_page_id:
        return

    token_data = get_facebook_access_tokens()

    deafember_page_token = require(get_page_token(token_data, deafember_page_id), "Could not find Deafember Page token.")
    if not deafember_page_token:
        return

    signs_of_fun_page_token = require(get_page_token(token_data, signs_of_fun_page_id), "Could not find Signs of Fun Page token.")
    if not signs_of_fun_page_token:
        return

    print("\n--- Starting Social Media Blast ---")
    # Facebook
    post_to_facebook_page(deafember_page_token, deafember_page_id, content) # Deafember Page
    print()
    signs_of_fun_facebook_post_id = post_to_facebook_page(signs_of_fun_page_token, signs_of_fun_page_id, content) # Signs of Fun Page
    print()

    # Instagram
    image_urls = get_image_urls_from_facebook_post(signs_of_fun_page_token, signs_of_fun_facebook_post_id)
    post_instagram_carousel(signs_of_fun_page_token, config.get('IG_USER_ID'), image_urls, content.message) # Signs of Fun Instagram
    print()

    # Twitter
    post_to_twitter(content)

if __name__ == "__main__":
    # Schedule the job every day at 12:00 (noon)
    print("\nScheduling daily check at 12:00 PM...")
    schedule.every().day.at("12:00").do(check_date_and_run)
    
    # Infinite loop to keep the script running and check for pending jobs
    while True:
        schedule.run_pending()
        time.sleep(60) # Check every minute
