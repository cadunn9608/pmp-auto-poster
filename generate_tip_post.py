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

# Clean up redundant prefixes case-insensitively
cleaned_tip = ai_tip_raw
prefixes_to_strip = [
    "pmp exam tip:", "pmp study tip:", "exam tip:", "study tip:", "tip:",
    "pmp exam tip", "pmp study tip", "exam tip", "study tip"
]
lower_tip = cleaned_tip.lower()
for p in prefixes_to_strip:
    if lower_tip.startswith(p):
        cleaned_tip = cleaned_tip[len(p):].strip()
        break

header_tag = "★ DAILY PMP TIP ★"
ai_tip_formatted = make_bold(cleaned_tip)

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
selected_setting = random.choice(settings_pool)

# 3. Generate Image Natively via Gemini with Pixar Animation Style explicitly enforced
image_prompt = (
    f"A high-end 3D animated digital art piece in the distinct visual style of Pixar and Disney, "
    f"featuring {selected_animals} inside {selected_setting}. "
    "Vibrant warm lighting, charming expressive characters, polished cinematic digital rendering, perfect composition."
)

print(f"Generating background image with prompt: {image_prompt}")

image_bytes = None
image_models_to_try = ["gemini-2.5-flash", "gemini-3.1-flash-image", "gemini-3.1-flash-image-preview"]

for img_model in image_models_to_try:
    try:
        response = client.models.generate_content(
            model=img_model,
            contents=image_prompt,
        )
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    break
            if image_bytes:
                break
        if image_bytes:
            print(f"Successfully generated background image using model: {img_model}")
            break
    except Exception as e:
        print(f"Image model {img_model} failed: {e}. Trying next...")

if not image_bytes:
    raise Exception("All Gemini image generation models failed to return image data.")

image_path = "temp_tip_image.png"

# 4. Process Image & Render Dynamically Sized Text Box Overlay
img = Image.open(BytesIO(image_bytes)).convert("RGBA")
img_width, img_height = img.size

try:
    font = ImageFont.truetype("DejaVuSans.ttf", 17)
    header_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
except IOError:
    font = ImageFont.load_default()
    header_font = font

# Wrap paragraphs cleanly
wrapped_lines = []
for paragraph in cleaned_tip.split("\n"):
    if paragraph.strip():
        wrapped_lines.extend(textwrap.wrap(paragraph.strip(), width=74))

# Dynamically compute box dimensions based on line count
line_height = 22
header_height = 30
padding = 25
total_text_height = (len(wrapped_lines) * line_height) + header_height + (padding * 2)

box_x0 = 40
box_x1 = img_width - 40
box_y1 = img_height - 30
box_y0 = box_y1 - total_text_height

overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
draw_overlay = ImageDraw.Draw(overlay)

draw_overlay.rounded_rectangle(
    [box_x0, box_y0, box_x1, box_y1], 
    radius=16, 
    fill=(15, 23, 42, 235), 
    outline=(59, 130, 246, 255), 
    width=3
)

img = Image.alpha_composite(img, overlay).convert("RGB")
draw = ImageDraw.Draw(img)

text_x = box_x0 + 22
text_y = box_y0 + 18

draw.text((text_x, text_y), header_tag, fill=(250, 204, 21, 255), font=header_font)
text_y += header_height

for line in wrapped_lines:
    draw.text((text_x, text_y), line, fill=(241, 245, 249, 255), font=font)
    text_y += line_height

img.save(image_path, "PNG")
print("Tip background image with dynamically fitted text overlay successfully generated and saved!")

# 5. Format Social Media Caption Text
post_header = make_bold("💡 DAILY PMP TIP 💡\n\n")
capm_link = "https://courses.velociteach.com/online-courses/capm-pta/?ref=nwvmngf&tm_daily_question=0806"

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

# 6. Exchange/Refresh Facebook Token
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

# 7. Post the Branded Photo + Caption to Facebook Page Feed
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
