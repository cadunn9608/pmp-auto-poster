import os
import time
import random
import textwrap
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types
from moviepy.editor import ImageClip, AudioFileClip
from gTTS import gTTS

def make_bold(text):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    return text.translate(str.maketrans(normal, bold))

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 1. Generate Structured PMP Exam Question Content with model fallbacks
pmp_prompt = (
    "Create a realistic PMP exam practice question with 4 multiple choice options (A, B, C, D), "
    "the correct answer, and a clear, concise explanation of why it is correct. "
    "Output only the question, options, answer, and explanation clearly."
)

pmp_content_raw = None
text_models_to_try = [
    "gemini-3.5-flash",
    "gemini-3.1-flash",
    "gemini-3.6-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite"
]

for model_name in text_models_to_try:
    print(f"Attempting question generation using model: {model_name}")
    try:
        response_text = client.models.generate_content(
            model=model_name,
            contents=pmp_prompt,
        )
        pmp_content_raw = response_text.text.strip()
        print(f"Successfully generated question using {model_name}!")
        break
    except Exception as e:
        print(f"Model {model_name} failed with error: {e}. Trying next...")
        time.sleep(5)

if not pmp_content_raw:
    raise Exception("All models failed to generate question content due to high demand.")

header_tag = "💡DAILY PMP EXAM PREP💡\n\n"
pmp_content_formatted = make_bold(pmp_content_raw)

# 2. Dynamic Randomization Pools for Unique Daily Backgrounds (9:16 vertical focus)
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
    f"A stunning 3D Pixar-style animated vertical 9:16 digital art illustration featuring {selected_animals} "
    f"collaborating and working on a project inside {selected_setting}. "
    "Bright cinematic lighting, charming details, vibrant professional colors, high quality 3D render."
)

# Image generation with built-in retry/fallback handling for errors
result_img = None
image_models_to_try = [
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
    "gemini-3.1-flash-lite-image",
    "gemini-2.5-flash-image",
    "gemini-3.5-flash"
]

print(f"Generating random daily image: {selected_animals} in {selected_setting}...")
for img_model in image_models_to_try:
    try:
        print(f"Attempting image generation using model: {img_model}")
        result_img = client.models.generate_content(
            model=img_model,
            contents=image_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )
        break
    except Exception as e:
        print(f"Image model {img_model} failed with error: {e}. Retrying...")
        time.sleep(10)

if not result_img:
    raise Exception("All image generation models failed due to high demand or server errors.")

image_path = "daily_pmp_tip.jpg"
image_bytes = None
for part in result_img.candidates[0].content.parts:
    if part.inline_data:
        image_bytes = BytesIO(part.inline_data.data)
        break

if not image_bytes:
    raise Exception("Failed to generate and extract image bytes from Gemini response.")

# 3. Overlay with Corrected Margins and Safe Wrapping
print("Overlaying PMP question on image...")
img = Image.open(image_bytes).convert("RGB")
width, height = img.size

font_size = max(20, int(height * 0.025))
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
except IOError:
    font = ImageFont.load_default()

draw = ImageDraw.Draw(img)

margin = int(width * 0.06)
text_box_w = width - (2 * margin)

char_limit = int(text_box_w / (font_size * 0.52))
wrapped_lines = textwrap.wrap(pmp_content_raw, width=char_limit)

line_height = font_size + 8
text_box_h = (len(wrapped_lines) * line_height) + 36

text_box_y = height - text_box_h - int(height * 0.04)
text_box_x = margin

overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)
overlay_draw.rounded_rectangle(
    [text_box_x, text_box_y, text_box_x + text_box_w, text_box_y + text_box_h],
    radius=18,
    fill=(15, 23, 42, 245),
    outline=(255, 255, 255, 180),
    width=3
)
img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
draw = ImageDraw.Draw(img)

current_y = text_box_y + 18
for line in wrapped_lines:
    draw.text((text_box_x + 18, current_y), line, fill="white", font=font)
    current_y += line_height

img.save(image_path)
print("Image and text overlay successfully created!")

# 4. Generate Voiceover Audio & Assemble 90-Second Video Reel
print("Generating audio voiceover...")
audio_text = (
    "Here is your daily PMP exam question. "
    f"{pmp_content_raw} "
    "Pause for a moment to think about your answer. "
    "Now let's review the correct answer and explanation."
)
tts = gTTS(text=audio_text, lang='en', slow=False)
audio_path = "temp_voiceover.mp3"
tts.save(audio_path)

print("Building vertical video reel with MoviePy...")
audio_clip = AudioFileClip(audio_path)
video_duration = max(90.0, audio_clip.duration)

image_clip = ImageClip(image_path).set_duration(video_duration)
video_clip = image_clip.set_audio(audio_clip)

video_clip = video_clip.resize(height=1920)
if video_clip.w > 1080:
    video_clip = video_clip.crop(x_center=video_clip.w/2, width=1080)

output_video_path = "daily_pmp_reel.mp4"
video_clip.write_videofile(
    output_video_path,
    fps=24,
    codec='libx264',
    audio_codec='aac',
    preset='medium'
)
print("Video reel successfully generated and saved!")

# 5. Format Social Media Caption Text
post_header = make_bold(header_tag)
cta_block = (
    "\n\n👇 " + make_bold("READY TO PASS YOUR PMP EXAM ON THE FIRST TRY?") + "\n" +
    make_bold("Join top-rated training with Velociteach:") + "\n" +
    "https://www.velociteach.com/"
)
post_text = post_header + pmp_content_formatted + cta_block

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

# 7. Post the Video Reel to Facebook Page
page_id = os.environ["FACEBOOK_PAGE_ID"]

print("Initializing Facebook Reels upload container...")
init_url = f"https://graph.facebook.com/v18.0/{page_id}/videos"
init_payload = {
    "upload_phase": "start",
    "access_token": active_token
}
init_res = requests.post(init_url, data=init_payload).json()
video_id = init_res.get("video_id")
upload_url = init_res.get("upload_url")

if not upload_url:
    raise Exception(f"Failed to initialize Facebook video upload container: {init_res}")

print("Uploading video file chunks to Facebook...")
with open(output_video_path, "rb") as video_file:
    headers = {"Authorization": f"OAuth {active_token}"}
    upload_res = requests.post(upload_url, data=video_file, headers=headers)
    print("Upload response:", upload_res.json())

print("Publishing video container as a Reel...")
publish_payload = {
    "video_id": video_id,
    "upload_phase": "finish",
    "media_type": "REELS",
    "description": post_text,
    "access_token": active_token
}
final_res = requests.post(init_url, data=publish_payload)
print("Facebook Reels Publish Response:", final_res.json())
