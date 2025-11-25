import requests
import json
import tweepy
from tiktok_uploader.upload import upload_video # Unofficial wrapper
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

# POST CONTENT
MESSAGE = "Hello world! This is a test post across all platforms. #testing"
IMAGE_PATH = "./image.jpg" # Required for Insta/FB
VIDEO_PATH = "./video.mp4" # Required for TikTok (and optional for others)

# ==============================================================================
# PLATFORM FUNCTIONS
# ==============================================================================

def post_to_facebook_page():
    url = f"https://graph.facebook.com/v19.0/{config.get('FB_PAGE_ID')}/photos"
    payload = {
        'message': MESSAGE,
        'access_token': config.get('META_ACCESS_TOKEN')
    }
    files = {
        'source': open(IMAGE_PATH, 'rb')
    }
    r = requests.post(url, data=payload, files=files)
    if r.status_code == 200:
        print(f"✅ Posted to FB Page: {r.json().get('id')}")
    else:
        print(f"❌ FB Page Error: {r.text}")

def post_to_facebook_group():
    # NOTE: You must add your "App" to the Group's settings manually on Facebook
    url = f"https://graph.facebook.com/v19.0/{config.get('FB_GROUP_ID')}/photos"
    payload = {
        'message': MESSAGE,
        'access_token': config.get('META_ACCESS_TOKEN')
    }
    files = {
        'source': open(IMAGE_PATH, 'rb')
    }
    r = requests.post(url, data=payload, files=files)
    if r.status_code == 200:
        print(f"✅ Posted to FB Group: {r.json().get('id')}")
    else:
        print(f"❌ FB Group Error: {r.text}")

def post_to_instagram():
    # Step 1: Create Container
    url_create = f"https://graph.facebook.com/v19.0/{config.get('IG_USER_ID')}/media"
    # Note: Instagram Graph API requires the image be on a PUBLIC URL, not local.
    # For this script, we assume you host it somewhere or use a service like Imgur temporarily.
    # If you must upload local, you need a specialized tool. 
    # Here we assume `image_url` is passed or we skip local upload for this simplified script.
    print("⚠️ Instagram API requires a public image URL, not a local file path.")
    print("⚠️ Skipping Instagram for this local-file example.")
    # To implement: POST to /media with 'image_url', get ID, then POST to /media_publish

def post_to_twitter():
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
        media = api.media_upload(filename=IMAGE_PATH)
        # Create Tweet
        response = client.create_tweet(text=MESSAGE, media_ids=[media.media_id])
        print(f"✅ Posted to Twitter: {response.data['id']}")
    except Exception as e:
        print(f"❌ Twitter Error: {e}")

def post_to_tiktok():
    # Uses selenium to automate the browser upload
    # Requires 'tiktok-uploader' installed and a valid session ID
    try:
        upload_video(
            filename=VIDEO_PATH,
            description=MESSAGE,
            cookies=config.get('TIKTOK_SESSION_ID'),
            headless=True 
        )
        print("✅ Posted to TikTok")
    except Exception as e:
        print(f"❌ TikTok Error: {e}")

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

    return {
        "message": text,
        "attachments": [main_photo_path, list_photo_path]
    }

def january_post(today):
    FIRST_DEAFEMBER_YEAR = 2021
    last_year = today.year - 1
    annual_count = last_year - FIRST_DEAFEMBER_YEAR + 1

    return {
        "message": f"That's a wrap! Thank you for participating in our {num2words(annual_count, to='ordinal')}-annual Deaf-ember. Happy New Year! #deafember{last_year}",
        "attachments": ["./photos/63.png"]
    }


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def check_date_and_run():
    today = datetime.date.today()

    content = None

    # Check if today is in December
    if today.month == 12:
        content = december_post(today)
        
    # Check if today is January 1st (Month 1, Day 1)
    elif today.month == 1 and today.day == 1:
        content = january_post(today)
        
    # Otherwise do nothing
    else:
        return

    print("--- Starting Social Media Blast ---")
    # post_to_facebook_page()
    # post_to_facebook_group()
    # post_to_twitter()
    # post_to_tiktok()
    # post_to_instagram() # Requires hosting logic


if __name__ == "__main__":
    # Schedule the job every day at 12:00 (noon)
    schedule.every().day.at("12:00").do(check_date_and_run)
    
    # Infinite loop to keep the script running and check for pending jobs
    while True:
        schedule.run_pending()
        time.sleep(60) # Check every minute
