import os
import time
import random
import textwrap
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types

def make_bold(text):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    return text.translate(str.maketrans(normal, bold))

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 1. Generate the Daily PMP Tip Text with model fallbacks
tip_prompt = (
    "Create a short, punchy, high-value daily PMP exam study tip optimized for social media. "
    "Focus on a core project management principle, formula, or agile/predictive mindset concept. "
    "Output only the tip content without any Markdown formatting or emojis."
)

ai_tip_raw = None
text_models_to_try = [
    "gemini-3.5-flash",
    "gemini-3.1-flash",
    "gemini-3.6-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite"
]

for model_name in text_models_to_try:
    print(f"Attempting tip generation using model: {model_name}")
    try:
        response_text = client.models.generate_content(
            model=model_name,
            contents=tip_prompt,
        )
        ai_tip_raw = response_text.text.strip()
        print(f"Successfully generated tip using {model_name}!")
        break
    except Exception as e:
        print(f"Model {model_name} failed with error: {e}. Trying next...")
        time.sleep(5)

if not ai_tip_raw:
    raise Exception("All models failed to generate tip content due to high demand.")

header_tag = "💡DAILY PMP TIP💡\n\n"
ai_tip_formatted = make_bold(ai_tip_raw)

# 2. Dynamic Randomization Pools for Unique Daily Backgrounds
animals_pool = [
    "a fluffy golden retriever puppy and a playful orange kitten",
    "a joyful golden retriever puppy and a curious red panda",
    "a golden retriever puppy and a clever baby elephant wearing tiny glasses",
    "a cute golden retriever puppy and a friendly capybara",
    "a cheerful golden retriever puppy and an energetic fox kit",
    "a happy golden retriever puppy and a curious gecko",
    "a golden retriever and a bunny rabbit",
    "a senior golden retriever and a american bulldog mix puppy"
]

settings_pool = [
    "a modern sunlit tech startup open-office with colorful beanbag chairs and whiteboards",
    "a cozy rustic wooden treehouse study room surrounded by green forest canopy views",
    "a futuristic sci-fi command center with glowing holographic project schedules",
    "a bright beachside patio overlooking the ocean with tropical plants and sunny skies",
    "a vintage artisan workshop filled with creative blueprints, tools, and warm lighting",
    "a vintage tech workshop filled with gadgets, tools, and warm lighting",
    "a modern tech startup conference room",
    "a college library study table"
]

selected_animals = random.choice(animals_pool)
@@ -164,40 +168,51 @@
img.save(image_path)
print("Text box margins and wrapping successfully corrected!")

# 4. Format Social Media Caption Text
# 4. Format Social Media Caption Text (UPDATED FOR VELOCITEACH CAPM)
post_header = make_bold(header_tag)
cta_block = (
    "\n\n👇 " + make_bold("READY TO PASS YOUR PMP EXAM ON THE FIRST TRY?") + "\n" +
    make_bold("Join 50,000 other students from 180 countries in top-rated training with Master of Project Academy:") + "\n" +
    "https://masterofproject.com/"
)

capm_link = "https://courses.velociteach.com/online-courses/capm-pta/?ref=nwvmngf&tm_daily_question=0806"

# Rotating CTAs to prevent Facebook from flagging posts as repetitive spam
capm_ctas = [
    "👇 " + make_bold("NOT QUITE READY FOR THE PMP? BUILD YOUR FOUNDATION FIRST!") + "\n" +
    f"Test your knowledge with Velociteach's full 3-hour CAPM Practice Test for $89:\n{capm_link}",
    
    "👇 " + make_bold("BUILDING YOUR PROJECT MANAGEMENT CAREER?") + "\n" +
    f"The CAPM is the perfect stepping stone to the PMP. Try this comprehensive 3-hour practice exam from Velociteach:\n{capm_link}",
    
    "👇 " + make_bold("WANT TO TEST YOUR BASELINE KNOWLEDGE?") + "\n" +
    f"See where you stand with this complete 3-hour CAPM practice exam from Velociteach:\n{capm_link}"
]

cta_block = "\n\n" + random.choice(capm_ctas)
post_text = post_header + ai_tip_formatted + cta_block

# 5. Exchange/Refresh Facebook Token
app_id = os.environ["FACEBOOK_APP_ID"]
app_secret = os.environ["FACEBOOK_APP_SECRET"]
current_token = os.environ["FACEBOOK_ACCESS_TOKEN"]

refresh_url = "https://graph.facebook.com/v18.0/oauth/access_token"
refresh_params = {
    "grant_type": "fb_exchange_token",
    "client_id": app_id,
    "client_secret": app_secret,
    "fb_exchange_token": current_token
}
refresh_res = requests.get(refresh_url, params=refresh_params).json()
active_token = refresh_res.get("access_token", current_token)

# 6. Post the Branded Photo + Caption to Facebook Page Feed
page_id = os.environ["FACEBOOK_PAGE_ID"]
post_url = f"https://graph.facebook.com/v18.0/{page_id}/photos"

with open(image_path, "rb") as img_file:
    files = {"source": img_file}
    payload = {
        "caption": post_text,
        "published": "true",
        "access_token": active_token
    }
    res = requests.post(post_url, data=payload, files=files)
    print("Facebook Photo Post Response:", res.json())
