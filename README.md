# Install Required Libraries 
In the repo's root directory, run the following command: 
`pip install -r requirements.txt`

# Setup Needed Keys
Using the .env-example file as a guide, create an .env file and fill in the values as follows:
## Facebook & Instagram (Meta)
1. **TODO**

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