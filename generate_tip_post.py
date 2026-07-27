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
    bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝗅𝗭𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    return text.translate(str.maketrans(normal, bold))

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 1. Generate the Daily PMP Tip Text with robust model fallbacks
tip_prompt = (
    "Create a short, punchy, high-value daily PMP exam study tip optimized for social media. "
    "Focus on a core project management principle, formula, or agile/predictive mindset concept. "
    "Output only the tip content without any Markdown formatting or emojis."
)

ai_tip_raw = None
models_to_try = ["gemini-3.5-flash", "gemini-2.5-flash"]

for model_name in models_to_try:
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
    "a cheerful golden retriever puppy and an energetic fox kit"
]

settings_pool = [
    "a modern sunlit tech startup open-office with colorful beanbag chairs and whiteboards",
    "a cozy rustic wooden treehouse study room surrounded by green forest canopy views",
    "a futuristic sci-fi command center with glowing holographic project schedules",
    "a bright beachside patio overlooking the ocean with tropical plants and sunny skies",
    "a vintage artisan workshop filled with creative blueprints, tools, and warm lighting"
]

selected_animals = random.choice(animals_pool)
selected_setting = random.choice(settings_pool)

image_prompt = (
    f"A stunning 3D Pixar-style animated digital art illustration featuring {selected_animals} "
    f"collaborating and working on a project inside {selected_setting}. "
    "Bright cinematic lighting, charming details, vibrant professional colors, high quality 3D render."
)

print(f"Generating random daily image: {selected_animals} in {selected_setting}...")
result_img = client.models.generate_content(
    model="gemini-3.1-flash-image",
    contents=image_prompt,
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"]
    )
)

image_path = "daily_pmp_tip.jpg"
image_bytes = None
for part in result_img.candidates[0].content.parts:
    if part.inline_data:
        image_bytes = BytesIO(part.inline_data.data)
        break

if not image_bytes:
    raise Exception("Failed to generate and extract image bytes from Gemini response.")

# 3. Overlay with Larger Font and Positioned Slightly Higher Up
print("Overlaying PMP tip on image...")
img = Image.open(image_bytes).convert("RGB")
width, height = img.size

# Larger font size for maximum visual impact (~3.6% of height)
font_size = max(20, int(height * 0.036))
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
except IOError:
    font = ImageFont.load_default()

draw = ImageDraw.Draw(img)

margin = int(width * 0.04)
text_box_w = width - (2 * margin)

char_limit = int(text_box_w / (font_size * 0.48))
wrapped_lines = textwrap.wrap(ai_tip_raw, width=char_limit)

line_height = font_size + 12
text_box_h = (len(wrapped_lines) * line_height) + 44

# Positioned slightly higher up from the bottom edge
text_box_y = height - text_box_h - int(height * 0.09)
text_box_x = margin

# Draw semi-transparent dark background box with crisp borders
overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)
overlay_draw.rounded_rectangle(
    [text_box_x, text_box_y, text_box_x + text_box_w, text_box_y + text_box_h],
    radius=18,
    fill=(15, 23, 42, 240),
    outline=(255, 255, 255, 160),
    width=3
)
img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
draw = ImageDraw.Draw(img)

current_y = text_box_y + 22
for line in wrapped_lines:
    draw.text((text_box_x + 22, current_y), line, fill="white", font=font)
    current_y += line_height

img.save(image_path)
print("Updated higher position and larger font applied successfully!")

# 4. Format Social Media Caption Text
post_header = make_bold(header_tag)
cta_block = (
    "\n\n👇 " + make_bold("READY TO PASS YOUR PMP EXAM ON THE FIRST TRY?") + "\n" +
    make_bold("Join 50,000 other students from 180 countries in top-rated training with Master of Project Academy:") + "\n" +
    "https://masterofproject.com/"
)
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
