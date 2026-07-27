import os
import time
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

# 1. Generate the Daily PMP Tip Text
tip_prompt = (
    "Create a short, punchy, high-value daily PMP exam study tip optimized for social media. "
    "Focus on a core project management principle, formula, or agile/predictive mindset concept. "
    "Output only the tip content without any Markdown formatting or emojis."
)

response_text = client.models.generate_content(
    model="gemini-3.5-flash",
    contents=tip_prompt,
)
ai_tip_raw = response_text.text.strip()

header_tag = "💡DAILY PMP TIP💡\n\n"
ai_tip_formatted = make_bold(ai_tip_raw)

# 2. Generate 3D Pixar-style animated image with cute animals (unique every day)
image_prompt = (
    "A stunning 3D Pixar-style animated digital art illustration featuring an adorable, fluffy golden retriever puppy "
    "and a cute koala wearing tiny glasses studying project management together at a cozy wooden desk. "
    "Bright, vibrant cinematic lighting, charming details, colorful office background, high quality 3D render."
)

print("Generating daily Pixar-style branded image...")
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

# 3. Overlay the PMP Tip Text cleanly on the Generated Image using Pillow (with larger box & font)
print("Overlaying PMP tip on image...")
img = Image.open(image_bytes).convert("RGB")
width, height = img.size

# Increased font size for better readability (~3.2% of total image height)
font_size = max(18, int(height * 0.032))
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
except IOError:
    font = ImageFont.load_default()

draw = ImageDraw.Draw(img)

# Wider margin and larger text container box
margin = int(width * 0.04)
text_box_w = width - (2 * margin)

char_limit = int(text_box_w / (font_size * 0.50))
wrapped_lines = textwrap.wrap(ai_tip_raw, width=char_limit)

line_height = font_size + 10
text_box_h = (len(wrapped_lines) * line_height) + 40
text_box_y = height - text_box_h - int(height * 0.05)
text_box_x = margin

# Draw a larger semi-transparent dark background box for high contrast and readability
overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)
overlay_draw.rounded_rectangle(
    [text_box_x, text_box_y, text_box_x + text_box_w, text_box_y + text_box_h],
    radius=16,
    fill=(15, 23, 42, 235),
    outline=(255, 255, 255, 140),
    width=3
)
img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
draw = ImageDraw.Draw(img)

current_y = text_box_y + 20
for line in wrapped_lines:
    draw.text((text_box_x + 20, current_y), line, fill="white", font=font)
    current_y += line_height

img.save(image_path)
print("Larger branded text box successfully applied!")

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
