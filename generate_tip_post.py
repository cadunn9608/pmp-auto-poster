import os
import time
import random
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

# 1. Generate a concise Daily PMP Tip Text optimized for image overlays
tip_prompt = (
    "Create a very short, punchy, high-value daily PMP exam study tip (maximum 3 short sentences total). "
    "Focus on a core project management principle or mindset rule. "
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

# 2. Expanded Dynamic Randomization Pools for Unique Daily Backgrounds
animals_pool = [
    # Original Pool
    "a fluffy golden retriever puppy and a playful orange kitten",
    "a joyful golden retriever puppy and a curious red panda",
    "a golden retriever puppy and a clever baby elephant wearing tiny glasses",
    "a cute golden retriever puppy and a friendly capybara",
    "a cheerful golden retriever puppy and an energetic fox kit",
    "a happy golden retriever puppy and a curious gecko",
    "a golden retriever and a bunny rabbit",
    "a senior golden retriever and an American bulldog mix puppy",
    # 15 New Characters (Including Petey & PMP Training Companions)
    "Andrew the golden retriever puppy teaching Petey, a loyal white-and-black pit bull mix with a distinct black patch over his left eye",
    "Andrew the golden retriever puppy studying alongside Barnaby, a tall bespectacled giraffe wearing a tweed vest",
    "Andrew the golden retriever puppy mentoring Professor Pip, a clever little field mouse with tiny wire-rimmed spectacles",
    "Andrew the golden retriever puppy collaborating with Maya, an energetic spider monkey wearing a bright yellow safety helmet",
    "Andrew the golden retriever puppy taking notes from Winston, a wise old owl with a bowtie perched on reference books",
    "Andrew the golden retriever puppy reviewing blueprints with Cleo, a sleek Siamese cat wearing an architect's hard hat",
    "Andrew the golden retriever puppy working with Buster, a stout bulldog wearing a security guard cap and holding a clipboard",
    "Andrew the golden retriever puppy brainstorming with Penny, a cheerful red panda wearing a polka-dot scarf",
    "Andrew the golden retriever puppy mentoring Oliver, a curious baby elephant wearing round glasses",
    "Andrew the golden retriever puppy analyzing data with Zoe, a sleek snow leopard wearing a tech vest",
    "Andrew the golden retriever puppy studying project schedules with Dexter, a studious beaver in a flannel shirt",
    "Andrew the golden retriever puppy grading papers with Luna, a gentle silver-furred fox wearing a silk scarf",
    "Andrew the golden retriever puppy organizing tasks with Sammy, an enthusiastic sea otter with a tool belt",
    "Andrew the golden retriever puppy reviewing a project charter with Felix, a sharp-dressed red fox in a necktie",
    "Andrew the golden retriever puppy carrying binders with Hazel, a fluffy squirrel wearing a knitted cardigan"
]

settings_pool = [
    # Original Pool
    "a modern sunlit tech startup open-office with colorful beanbag chairs and whiteboards",
    "a cozy rustic wooden treehouse study room surrounded by green forest canopy views",
    "a futuristic sci-fi command center with glowing holographic project schedules",
    "a bright beachside patio overlooking the ocean with tropical plants and sunny skies",
    "a vintage artisan workshop filled with creative blueprints, tools, and warm lighting",
    "a vintage tech workshop filled with gadgets, tools, and warm lighting",
    "a modern tech startup conference room",
    "a college library study table",
    # 15 New PMP Training & Student-Teacher Settings
    "a sunlit university lecture hall with tiered wooden desks and a large chalkboard covered in PMP network diagrams",
    "a cozy after-school study nook filled with floor cushions, glowing string lights, and PMP flashcards scattered across the table",
    "a modern corporate PMP training center equipped with ergonomic chairs, dual-monitor workstations, and a glass whiteboard showing an Agile sprint board",
    "a bustling campus library study carrel surrounded by towering PMBOK reference guidebooks and steaming mugs of coffee",
    "an outdoor courtyard PMP seminar under a sprawling oak tree with picnic tables and a portable whiteboard detailing risk management matrices",
    "a high-tech project management war room featuring glowing digital Gantt charts and Earned Value Management formulas on large wall displays",
    "a rustic wooden cabin study room with a crackling stone fireplace and vintage Work Breakdown Structure (WBS) charts pinned to the walls",
    "a bright architectural drafting studio cluttered with T-squares, scale rulers, and project schedule network logic diagrams",
    "a cheerful adult-education classroom featuring colorful alphabet blocks spelling out 'PMP' and collaborative break-out stations",
    "a rooftop terrace study garden surrounded by potted succulents, solar lanterns, and a panoramic city view while reviewing stakeholder engagement grids",
    "an underground PM workshop lit by Edison bulbs, filled with tinkering tools and a chalkboard mapping out critical path analysis",
    "a quiet museum archive room with polished mahogany tables, brass reading lamps, and historical project logs for case study reviews",
    "a sleek Silicon Valley incubator space with exposed brick walls, neon motivational agile quotes, and glass-walled Scrum review pods",
    "a serene botanical greenhouse classroom filled with lush ferns and a rustic wooden podium draped with PMP exam simulation guides",
    "a vintage mid-century modern home office featuring a teakwood desk, a retro rotary phone, and an organized Kanban board tracking project deliverables"
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

# 4. Process Image & Render Pixel-Perfect Text Box Overlay (Tip Only)
img = Image.open(BytesIO(image_bytes)).convert("RGBA")
img_width, img_height = img.size

try:
    font = ImageFont.truetype("DejaVuSans.ttf", 18)
    header_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
except IOError:
    font = ImageFont.load_default()
    header_font = font

box_x0 = 40
box_x1 = img_width - 40
max_text_width = (box_x1 - box_x0) - 50

wrapped_lines = []
for paragraph in cleaned_tip.split("\n"):
    if not paragraph.strip():
        continue
    words = paragraph.strip().split()
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.getlength(test_line) <= max_text_width:
            current_line = test_line
        else:
            if current_line:
                wrapped_lines.append(current_line)
            current_line = word
    if current_line:
        wrapped_lines.append(current_line)

line_height = 24
header_height = 32
padding = 20
total_box_height = header_height + (len(wrapped_lines) * line_height) + (padding * 2)

box_y1 = img_height - 30
box_y0 = box_y1 - total_box_height

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

text_x = box_x0 + 25
text_y = box_y0 + 16

draw.text((text_x, text_y), header_tag, fill=(250, 204, 21, 255), font=header_font)
text_y += header_height

for line in wrapped_lines:
    draw.text((text_x, text_y), line, fill=(241, 245, 249, 255), font=font)
    text_y += line_height

img.save(image_path, "PNG")
print("Tip background image with clean text overlay successfully generated and saved!")

# 5. Format Social Media Caption Text
post_header = make_bold("💡 DAILY PMP TIP 💡\n\n")
full_capm_url = "https://courses.velociteach.com/online-courses/capm-pta/?ref=nwvmngf&tm_daily_question=0806"

capm_ctas = [
    "👇 " + make_bold("NOT QUITE READY FOR THE PMP? BUILD YOUR FOUNDATION FIRST!") + "\n" +
    f"Test your knowledge with Velociteach's full 3-hour CAPM Practice Test for $89:\n{full_capm_url}",
    
    "👇 " + make_bold("BUILDING YOUR PROJECT MANAGEMENT CAREER?") + "\n" +
    f"The CAPM is the perfect stepping stone to the PMP. Try this comprehensive 3-hour practice exam from Velociteach:\n{full_capm_url}",
    
    "👇 " + make_bold("WANT TO TEST YOUR BASELINE KNOWLEDGE?") + "\n" +
    f"See where you stand with this complete 3-hour CAPM practice exam from Velociteach:\n{full_capm_url}"
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
