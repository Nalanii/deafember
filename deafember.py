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
def upload_unpublished_photo_on_facebook(access_token, image_source):
    url = f"{BASE_FB_URL}/me/photos"
    
    payload = {
        'access_token': access_token,
        'published': 'false'
    }
       
    if not os.path.exists(image_source):
        print(f"❌ Error: File not found at {image_source}")
        return None
    # Open file in binary mode
    files = {'source': open(image_source, 'rb')}
    source_desc = f"File: {image_source}"

    try:
        print(f"   ⬆️  Uploading {source_desc}...")
        # Note: 'files' is handled automatically by requests as multipart/form-data
        response = requests.post(url, data=payload, files=files)
        data = response.json()
        
        if 'id' in data:
            print(f"   ✅ Uploaded photo ID: {data['id']}")
            return data['id']
        else:
            print(f"   ❌ Failed to upload photo: {data}")
            return None
    except Exception as e:
        print(f"   ❌ Exception uploading photo: {e}")
        return None
    finally:
        # Close file if it was opened
        if files:
            files['source'].close()

def get_facebook_access_tokens():
    url = f"{BASE_FB_URL}/me/accounts"
    payload = {
        'access_token': config.get('META_USER_ACCESS_TOKEN')
    }
    r = requests.get(url, params=payload)
    data = r.json()
    if r.status_code == 200:
        print(f"✅ Fetched FB Access Tokens")
        return data
    else:
        print(f"❌ FB Access Tokens Error: {r.text}")
        return []
    
def get_page_token(data, target_id):
    for page in data.get('data', []):
        if page.get('id') == target_id:
            return page.get('access_token')
    return None # Return None if the ID isn't found

def get_image_urls_from_facebook_post(access_token, post_id):
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
        print(f"⚠️ Could not extract URLs: {e}")
        
    return image_urls

# ==============================================================================
# PLATFORM POSTING FUNCTIONS
# ==============================================================================

def post_to_facebook_page(access_token: str, group_or_page_id: str, post_content: PostContent):
    url = f"{BASE_FB_URL}/{group_or_page_id}/feed"
   
    attached_media = []
    photo_ids = []
    for attachment in post_content.attachments:
        photo_id = upload_unpublished_photo_on_facebook(access_token, attachment)
        if photo_id:
            # Format required by Graph API: [{"media_fbid": "123"}, ...]
            attached_media.append({"media_fbid": photo_id})
            photo_ids.append(photo_id)

    payload = {
        'message': post_content.message,
        'attached_media': json.dumps(attached_media),
        'access_token': access_token
    }

    r = requests.post(url, data=payload)
    data = r.json()

    if r.status_code == 200:
        print(f"✅ Posted to FB Page: {data.get('id')}")
    else:
        print(f"❌ FB Page Error: {r.text}")
    
    return data.get('id') # Post ID

def post_instagram_carousel(access_token: str, ig_user_id: str, image_urls: list, caption: str):
    # --- PHASE 1: Create Individual Item Containers ---
    item_container_ids = []
    
    for url in image_urls:
        url_create = f"{BASE_FB_URL}/{ig_user_id}/media"
        payload = {
            'image_url': url,
            'is_carousel_item': 'true',  # CRITICAL: Marks this as a child item
            'access_token': access_token
        }
        
        r = requests.post(url_create, data=payload)
        data = r.json()
        
        if 'id' in data:
            item_container_ids.append(data['id'])
            print(f"   ↳ Created item container: {data['id']}")
        else:
            print(f"❌ Error creating item for {id}: {data}")
            return None

    if not item_container_ids:
        print("❌ No items were successfully created.")
        return None

    # --- PHASE 2: Create the Carousel (Parent) Container ---
    
    url_carousel = f"{BASE_FB_URL}/{ig_user_id}/media"
    payload = {
        'media_type': 'CAROUSEL',
        'caption': caption,
        'children': ','.join(item_container_ids), # List of IDs as CSV string
        'access_token': access_token
    }
    
    r = requests.post(url_carousel, data=payload)
    carousel_result = r.json()
    
    if 'id' not in carousel_result:
        print(f"❌ Error creating parent carousel: {carousel_result}")
        return None
        
    creation_id = carousel_result['id']
    print(f"📦 Carousel Parent Created: {creation_id}")

    # --- PHASE 3: Publish the Carousel ---
    
    url_publish = f"{BASE_FB_URL}/{ig_user_id}/media_publish"
    publish_payload = {
        'creation_id': creation_id,
        'access_token': access_token
    }
    
    r_publish = requests.post(url_publish, data=publish_payload)
    publish_result = r_publish.json()

    if 'id' in publish_result:
        print(f"✅ Carousel Published Successfully: {publish_result['id']}")
        return publish_result['id']
    else:
        print(f"❌ Error Publishing Carousel: {publish_result}")
        return None

def post_to_twitter(post_content: PostContent):
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
        print(f"✅ Posted to Twitter: {response.data['id']}")
    except Exception as e:
        print(f"❌ Twitter Error: {e}")

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
    
    print("--- Setup ---")
    
    deafember_page_id = config.get('FB_DEAFEMBER_PAGE_ID')
    if not deafember_page_id:
        print("❌ Deafember Page ID not set in config.")
        return
    
    signs_of_fun_page_id = config.get('FB_SOF_PAGE_ID')
    if not signs_of_fun_page_id:
        print("❌ Signs of Fun Page ID not set in config.")
        return
    
    token_data = get_facebook_access_tokens()

    deafember_page_token = get_page_token(token_data, deafember_page_id)
    if not deafember_page_token:
        print("❌ Could not find Deafember Page token.")
        return
    print("✅ Deafember Page token found:", deafember_page_token)
    
    signs_of_fun_page_token = get_page_token(token_data, signs_of_fun_page_id)
    if not signs_of_fun_page_token:
        print("❌ Could not find Signs of Fun Page token.")
        return
    print("✅ Signs of Fun Page token found:", signs_of_fun_page_token)

    print("--- Starting Social Media Blast ---")
    # Facebook
    post_to_facebook_page(deafember_page_token, deafember_page_id, content) # Deafember Page
    signs_of_fun_facebook_post_id = post_to_facebook_page(signs_of_fun_page_token, signs_of_fun_page_id, content) # Signs of Fun Page

    # Instagram
    image_urls = get_image_urls_from_facebook_post(signs_of_fun_page_token, signs_of_fun_facebook_post_id)
    post_instagram_carousel(signs_of_fun_page_token, config.get('IG_USER_ID'), image_urls, content.message) # Signs of Fun Instagram
    
    # Twitter
    post_to_twitter(content)

if __name__ == "__main__":
    # check_date_and_run()

    # Schedule the job every day at 12:00 (noon)
    print("Scheduling daily check at 12:00 PM...")
    schedule.every().day.at("12:00").do(check_date_and_run)
    
    # Infinite loop to keep the script running and check for pending jobs
    while True:
        schedule.run_pending()
        time.sleep(60) # Check every minute
