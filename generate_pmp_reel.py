import os
import time
import random
import textwrap
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip
from google import genai
from google.genai import types

def make_bold(text):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    return text.translate(str.maketrans(normal, bold))

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 1. Generate the PMP Reel Script/Text
reel_prompt = (
    "Create a short, engaging script for a daily PMP exam study tip video reel. "
    "Keep it punchy, focused on a core project management principle or mindset concept, "
    "and optimize it for a social media video voiceover. Do not include markdown headers or brackets."
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
    try:
        response_text = client.models.generate_content(
            model=model_name,
            contents=reel_prompt,
        )
        ai_reel_raw = response_text.text.strip()
        break
    except Exception:
        time.sleep(2)

if not ai_reel_raw:
    raise Exception("Failed to generate reel content.")

# 2. Generate Background Image for the Reel
image_prompt = (
    "A vibrant 3D Pixar-style animated background of a cute golden retriever puppy "
    "studying project management charts in a sunny modern workspace. High quality render."
)

result_img = None
image_models_to_try = [
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
    "gemini-3.1-flash-lite-image",
    "gemini-2.5-flash-image",
    "gemini-3.5-flash"
]

for img_model in image_models_to_try:
    try:
        result_img = client.models.generate_content(
            model=img_model,
            contents=image_prompt,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
        )
        break
    except Exception:
        time.sleep(2)

image_bytes = None
if result_img:
    for part in result_img.candidates[0].content.parts:
        if part.inline_data:
            image_bytes = BytesIO(part.inline_data.data)
            break

bg_image_path = "reel_bg.jpg"
if image_bytes:
    img = Image.open(image_bytes).convert("RGB")
    img.save(bg_image_path)
else:
    img = Image.new("RGB", (1080, 1920), color=(15, 23, 42))
    img.save(bg_image_path)

# 3. Generate Voiceover Audio using gTTS
print("Generating voiceover audio...")
audio_path = "voiceover.mp3"
tts = gTTS(text=ai_reel_raw, lang='en', slow=False)
tts.save(audio_path)

# 4. Compile Background Image, Text Overlay, and Audio into a Video with MoviePy
print("Compiling video reel with text overlays and audio...")
video_filename = "daily_pmp_reel.mp4"
audio_clip = AudioFileClip(audio_path)
image_clip = ImageClip(bg_image_path).set_duration(audio_clip.duration)

# Create overlaid dynamic text clip for the video screen
wrapped_text = "\n".join(textwrap.wrap(ai_reel_raw, width=32))
txt_clip = TextClip(
    wrapped_text,
    fontsize=48,
    color='white',
    font='Arial-Bold',
    align='center',
    size=(1000, None)
).set_duration(audio_clip.duration).set_position(('center', 'center'))

# Composite image and text together, then attach audio
video_clip = CompositeVideoClip([image_clip, txt_clip]).set_audio(audio_clip)
video_clip.write_videofile(video_filename, fps=24, codec="libx264", audio_codec="aac")

# Cleanup temporary audio file
if os.path.exists(audio_path):
    os.remove(audio_path)

# 5. Format Caption Text
header_tag = "💡DAILY PMP REEL TIP💡\n\n"
ai_reel_formatted = make_bold(ai_reel_raw)
cta_block = (
    "\n\n👇 " + make_bold("READY TO PASS YOUR PMP EXAM ON THE FIRST TRY?") + "\n" +
    make_bold("Join 50,000 other students from 180 countries in top-rated training with Master of Project Academy:") + "\n" +
    "https://masterofproject.com/"
)
post_text = header_tag + ai_reel_formatted + cta_block

# 6. Exchange/Refresh Facebook Token using complete credentials
app_id = os.environ["FACEBOOK_APP_ID"]
app_secret = os.environ["FACEBOOK_APP_SECRET"]
current_token = os.environ["FACEBOOK_ACCESS_TOKEN"]
page_id = os.environ["FACEBOOK_PAGE_ID"]

refresh_url = "https://graph.facebook.com/v18.0/oauth/access_token"
refresh_params = {
    "grant_type": "fb_exchange_token",
    "client_id": app_id,
    "client_secret": app_secret,
    "fb_exchange_token": current_token
}
refresh_res = requests.get(refresh_url, params=refresh_params).json()
active_token = refresh_res.get("access_token", current_token)

# 7. Post the Reel/Video to Facebook Page
post_url = f"https://graph.facebook.com/v18.0/{page_id}/videos"

with open(video_filename, "rb") as video_file:
    files = {"source": video_file}
    payload = {
        "description": post_text,
        "access_token": active_token
    }
    res = requests.post(post_url, data=payload, files=files)
    print("Facebook Reel Post Response:", res.json())
