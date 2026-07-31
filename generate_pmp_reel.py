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
    bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝗳𝟴𝟵"
    return text.translate(str.maketrans(normal, bold))

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 1. Generate the PMP Reel Script/Text with robust fallback list
reel_prompt = (
    "Create a short, engaging script for a daily PMP exam study tip video reel. "
    "Keep it punchy, focused on a core project management principle or mindset concept, "
    "and optimize it for a social media video voiceover."
)

ai_reel_raw = None
text_models_to_try = [
    "gemini-3.5-flash",
    "gemini-3.1-flash",
    "gemini-3.6-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite"
]

for model_name in text_models_to_try:
    print(f"Attempting reel generation using model: {model_name}")
    try:
        response_text = client.models.generate_content(
            model=model_name,
            contents=reel_prompt,
        )
        ai_reel_raw = response_text.text.strip()
        print(f"Successfully generated reel text using {model_name}!")
        break
    except Exception as e:
        print(f"Model {model_name} failed with error: {e}. Trying next...")
        time.sleep(5)

if not ai_reel_raw:
    raise Exception("All models failed to generate reel content due to high demand.")

print("Reel text ready:", ai_reel_raw[:100], "...")

# Note: Add your video generation or ffmpeg processing steps below if your script compiles a video.
# (If your script expects environment variables for posting, ensure FACEBOOK_APP_ID, etc., are configured in GitHub Actions secrets.)
