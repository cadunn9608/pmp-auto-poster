import os
import time
import textwrap
import requests
from io import BytesIO
from PIL import Image
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip
from google import genai
from google.genai import types

def make_bold(text):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    return text.translate(str.maketrans(normal, bold))

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 1. Generate Multi-Scene Script from Gemini
script_prompt = (
    "Create a 90-second multi-scene script for a daily PMP exam study tip video reel. "
    "Break it down into 3 distinct scenes: "
    "Scene 1: Introduction with Andrew the golden retriever puppy introducing a tricky PMP scenario. "
    "Scene 2: The core project management principle or mindset breakdown with a supporting character. "
    "Scene 3: The takeaway and call to action. "
    "Return the output as plain text with clear scene markers like [SCENE 1], [SCENE 2], [SCENE 3]."
)

ai_script_raw = None
text_models_to_try = [
    "gemini-2.0-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash",
    "gemini-3.6-flash"
]

for model_name in text_models_to_try:
    try:
        response_text = client.models.generate_content(
            model=model_name,
            contents=script_prompt,
        )
        ai_script_raw = response_text.text.strip()
        break
    except Exception:
        time.sleep(2)

if not ai_script_raw:
    raise Exception("Failed to generate multi-scene script.")

print("Multi-scene script generated successfully!")

# 2. Split script into scenes and generate corresponding 3D Pixar-style visuals
scene_visual_prompts = [
    (
        "A vibrant 3D Pixar-style vertical 9:16 portrait of Andrew the golden retriever puppy "
        "sitting at a modern desk in a sunny office setting, looking charismatic and welcoming."
    ),
    (
        "A vibrant 3D Pixar-style vertical 9:16 portrait of Andrew the golden retriever puppy "
        "collaborating with a friendly cat project manager over colorful project agile boards and charts."
    ),
    (
        "A vibrant 3D Pixar-style vertical 9:16 portrait of Andrew the golden retriever puppy "
        "smiling triumphantly next to a glowing PMP pass certificate and milestone board."
    )
]

scene_clips = []
scene_texts = ai_script_raw.split("[SCENE")

# Filter out empty or header fragments
valid_scenes = [s for s in scene_texts if "]" in s]

for i, scene_content in enumerate(valid_scenes[:3]):
    # Clean text for voiceover
    clean_text = scene_content.split("]", 1)[1].strip()
    
    print(f"Processing Scene {i+1}...")
    
    # Generate image asset for this scene
    result_img = None
    for img_model in ["gemini-2.5-flash-image", "gemini-3.1-flash-image", "gemini-3.5-flash"]:
        try:
            result_img = client.models.generate_content(
                model=img_model,
                contents=scene_visual_prompts[i],
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

    img_path = f"scene_{i+1}.jpg"
    if image_bytes:
        img = Image.open(image_bytes).convert("RGB")
        img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
        img.save(img_path)
    else:
        img = Image.new("RGB", (1080, 1920), color=(15, 23, 42))
        img.save(img_path)

    # Generate Voiceover Audio for this scene
    audio_path = f"scene_{i+1}.mp3"
    tts = gTTS(text=clean_text, lang='en', slow=False)
    tts.save(audio_path)

    # Combine image and audio clip for the scene
    audio_clip = AudioFileClip(audio_path)
    img_clip = ImageClip(img_path).set_duration(audio_clip.duration)
    
    # Add subtle text overlay of key points
    wrapped = "\n".join(textwrap.wrap(clean_text[:120] + "...", width=32))
    txt_clip = TextClip(
        wrapped,
        fontsize=42,
        color='white',
        font='Arial-Bold',
        align='center',
        size=(1000, None)
    ).set_duration(audio_clip.duration).set_position(('center', 'center'))

    scene_video = CompositeVideoClip([img_clip, txt_clip]).set_audio(audio_clip)
    scene_clips.append(scene_video)

# 3. Concatenate all scenes into a 90+ second final video reel
print("Concatenating scenes into final 90+ second video...")
final_reel_clip = concatenate_videoclips(scene_clips)
video_filename = "daily_pmp_reel.mp4"
final_reel_clip.write_videofile(video_filename, fps=24, codec="libx264", audio_codec="aac")

# Cleanup temp files
for i in range(3):
    if os.path.exists(f"scene_{i+1}.jpg"):
        os.remove(f"scene_{i+1}.jpg")
    if os.path.exists(f"scene_{i+1}.mp3"):
        os.remove(f"scene_{i+1}.mp3")

# 4. Format Caption Text & Post to Facebook
header_tag = "💡DAILY PMP REEL TIP💡\n\n"
ai_reel_formatted = make_bold(ai_script_raw[:300] + "...")
cta_block = (
    "\n\n👇 " + make_bold("READY TO PASS YOUR PMP EXAM ON THE FIRST TRY?") + "\n" +
    make_bold("Join 50,000 other students from 180 countries in top-rated training with Master of Project Academy:") + "\n" +
    "https://masterofproject.com/"
)
post_text = header_tag + ai_reel_formatted + cta_block

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

post_url = f"https://graph.facebook.com/v18.0/{page_id}/videos"
with open(video_filename, "rb") as video_file:
    files = {"source": video_file}
    payload = {
        "description": post_text,
        "access_token": active_token
    }
    res = requests.post(post_url, data=payload, files=files)
    print("Facebook Reel Post Response:", res.json())
