import os
import sys
import json
import time
import subprocess
import random
import requests
import asyncio
import traceback
import edge_tts
from google import genai
from PIL import Image
from io import BytesIO

import builtins
def print(*args, **kwargs):
    kwargs['flush'] = True
    builtins.print(*args, **kwargs)

print("🚀 SCRIPT INITIATED: Clean Video & Natural Voice Pipeline...")

# ==============================================================================
# CONFIGURATION & ABSOLUTE PATH SETUP
# ==============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

GENERATED_IMAGE = os.path.join(ROOT_DIR, "host_character.png")
VOICE_AUDIO_MP3 = os.path.join(ROOT_DIR, "speech_original.mp3")
VIDEO_LIPSYNC = os.path.join(ROOT_DIR, "talking_head.mp4")
FINAL_REEL = os.path.join(ROOT_DIR, "daily_pmp_reel.mp4")

# ==============================================================================
# ENVIRONMENT VALIDATION
# ==============================================================================
def validate_environment():
    missing = []
    if not GEMINI_API_KEY or not GEMINI_API_KEY.strip(): missing.append("GEMINI_API_KEY")
    if not FB_PAGE_ID or not FB_PAGE_ID.strip(): missing.append("FB_PAGE_ID")
    if not FB_ACCESS_TOKEN or not FB_ACCESS_TOKEN.strip(): missing.append("FB_ACCESS_TOKEN")
    if missing:
        raise ValueError(f"❌ Critical environment variables missing: {missing}")
    print("✅ Environment variables validated.")

# ==============================================================================
# STEP 1: RANDOMIZED PMBOK TOPIC POOL
# ==============================================================================
pmp_reel_topics = [
    "agile team facilitation, servant leadership, and servant-leader mindset",
    "risk management, response strategies, and quantitative/qualitative risk analysis",
    "stakeholder engagement, communication planning, and managing expectations",
    "earned value management (EVM), schedule variance (SV), and cost variance (CV)",
    "change control procedures, integrated change control, and scope baseline management",
    "resource management, team charter, conflict resolution, and performance appraisals",
    "procurement management, contract types (fixed-price vs cost-reimbursable), and vendor selection",
    "quality management, cost of quality, process improvements, and quality control metrics",
    "agile ceremonies, backlog refinement, sprint planning, and velocity tracking",
    "project governance, compliance, benefits realization, and business value delivery",
    "project charter, assumption logs, and stakeholder registers",
    "schedule network analysis, critical path method, and lead/lag tactics"
]

character_settings_pool = [
    "Andrew the golden retriever wearing a tiny project management hard hat and holding a clipboard inside a modern sunlit tech startup open-office",
    "Andrew the golden retriever puppy collaborating with Petey, a clever white-and-black pit bull mix with a black patch over his left eye, inside a cozy rustic wooden treehouse study room",
    "a charismatic 3D animated ginger cat wearing a sleek headset inside a futuristic sci-fi command center with glowing holographic project schedules",
    "an enthusiastic 3D animated golden retriever puppy wearing tropical sunglasses on a bright beachside patio overlooking the ocean",
    "Andrew the golden retriever reviewing agile boards alongside Petey, an energetic white-and-black pit bull mix with a unique black patch over his left eye, in a vintage tech workshop",
    "a smart 3D animated border collie wearing professor glasses in a sunlit university lecture hall with tiered wooden desks",
    "a focused 3D animated silver fox wearing a sharp business suit inside a high-tech project management war room featuring digital Gantt charts",
    "an energetic 3D animated brown bear wearing a hoodie inside a sleek Silicon Valley incubator space with exposed brick walls",
    "Andrew the golden retriever and Petey, a white-and-black pit bull mix with a black patch over his left eye, brainstorming around a glass conference table with sticky notes",
    "a wise old 3D animated owl wearing a graduation cap sitting inside a cozy wood-paneled library surrounded by PMBOK guide books",
    "an ambitious 3D animated red panda pointing at a colorful Kanban agile board covered in sticky notes",
    "a professional 3D animated beagle wearing a navy blue blazer inside a high-rise corporate executive boardroom",
    "a tech-savvy 3D animated squirrel typing furiously on multiple monitors inside a sleek data analytics laboratory",
    "an adventurous 3D animated husky puppy reviewing project milestones next to a warm campfire under a starry night sky",
    "Andrew the golden retriever puppy holding a colorful Gantt chart in a minimalist Pixar-style digital design studio with vibrant lighting",
    "a tough 3D animated bulldog wearing a high-visibility safety vest inside a project site management trailer",
    "a trendy 3D animated otter wearing stylish round glasses inside a sunlit creative agency loft with indoor plants",
    "a sharp 3D animated rabbit wearing a pinstripe vest standing on a glass balcony overlooking a bustling financial district",
    "a cheerful 3D animated kangaroo holding architectural blueprints inside a futuristic glass innovation hub",
    "an eco-friendly 3D animated koala managing sustainability project metrics inside a sunlit glass greenhouse studio"
]

# ==============================================================================
# STEP 2: GEMINI GENERATES PMP CONTENT
# ==============================================================================
def get_daily_pmp_content():
    print("1️⃣ Fetching PMP question and script from Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    selected_topic = random.choice(pmp_reel_topics)
    
    prompt = (
        f"Create a rigorous, situational PMP exam practice question specifically focused on: {selected_topic}. "
        "Also write a highly engaging, punchy spoken script for the 3D animated animal host to read out loud. "
        "Keep the script concise (around 50 to 70 words) so it delivers a fast, high-impact challenge. "
        "Use question marks and clear ellipses (...) where the character should pause for dramatic effect. "
        "Output strictly as a valid JSON object with the following keys:\n"
        "{\n"
        f'    "topic": "{selected_topic}",\n'
        '    "question": "A situational PMP question description...",\n'
        '    "option_a": "A) First option text",\n'
        '    "option_b": "B) Second option text",\n'
        '    "option_c": "C) Third option text",\n'
        '    "option_d": "D) Fourth option text",\n'
        '    "correct_answer": "B) Second option text",\n'
        '    "explanation": "Concise PMP mindset explanation...",\n'
        '    "spoken_script": "Attention project managers! Here is a tricky PMP scenario about ' + selected_topic + '. Listen closely... What is your absolute best course of action here?"\n'
        "}"
    )
    
    models_to_try = ["gemini-3.5-flash", "gemini-3.1-flash", "gemini-1.5-flash", "gemini-3-flash-preview"]
    for attempt in range(1, 4):
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(model=model_name, contents=prompt, config={"response_mime_type": "application/json"})
                raw_text = response.text.strip()
                bt = chr(96) * 3
                if f"{bt}json" in raw_text: raw_text = raw_text.split(f"{bt}json")[1].split(bt)[0]
                elif bt in raw_text: raw_text = raw_text.split(bt)[1].split(bt)[0]
                return json.loads(raw_text.strip())
            except Exception:
                continue
        time.sleep(5)
    raise RuntimeError("Failed to generate content from Gemini.")

# ==============================================================================
# STEP 3: GENERATE CHARACTER PORTRAIT
# ==============================================================================
def generate_character_image():
    print("2️⃣ Generating Pixar-style character portrait via Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    selected_combo = random.choice(character_settings_pool)
    
    image_prompt = (
        f"A striking vertical 9:16 portrait shot in the distinct visual style of Pixar and Disney, "
        f"featuring {selected_combo}, "
        "facing the camera directly, head and shoulders framing, talking with an expressive open mouth and lively face, vibrant studio lighting, polished cinematic digital rendering."
    )
    
    for img_model in ["gemini-3.1-flash-image", "gemini-3.1-flash-image-preview", "gemini-1.5-pro"]:
        try:
            response = client.models.generate_content(model=img_model, contents=image_prompt)
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.inline_data and part.inline_data.data:
                        img = Image.open(BytesIO(part.inline_data.data)).convert("RGB")
                        img.save(GENERATED_IMAGE)
                        print("✅ Character image successfully saved!")
                        return
        except Exception:
            continue
    raise RuntimeError("Gemini image generation failed.")

# ==============================================================================
# STEP 4: EXPRESSIVE NEURAL VOICE (EDGE-TTS)
# ==============================================================================
async def generate_neural_voice(text):
    print("3️⃣ Generating expressive neural voice track with Edge-TTS...")
    # Using 'en-US-AndrewNeural' or 'en-US-BrianMultilingualNeural' for a warmer, less robotic tone
    communicate = edge_tts.Communicate(text, "en-US-BrianMultilingualNeural", rate="+5%", pitch="+0Hz")
    await communicate.save(VOICE_AUDIO_MP3)

# ==============================================================================
# STEP 5: ANIMATE MOUTH WITH WAV2LIP (CLEAN, NO PADDING)
# ==============================================================================
def animate_character_mouth():
    print("4️⃣ Animating character mouth with Wav2Lip...")
    wav2lip_dir = os.path.join(ROOT_DIR, "Wav2Lip")
    os.makedirs(os.path.join(wav2lip_dir, "temp"), exist_ok=True)
    
    checkpoint = os.path.join(wav2lip_dir, "checkpoints", "wav2lip_gan.pth")
    
    # Convert MP3 speech directly to WAV for Wav2Lip without padding so lips move continuously while talking
    wav_path = os.path.join(ROOT_DIR, "speech.wav")
    subprocess.run(["ffmpeg", "-y", "-i", VOICE_AUDIO_MP3, wav_path], check=True, capture_output=True)
    
    cmd = [
        "python", "inference.py", 
        "--checkpoint_path", checkpoint,
        "--face", GENERATED_IMAGE,
        "--audio", wav_path, 
        "--outfile", VIDEO_LIPSYNC,
        "--nosmooth" 
    ]
    
    res = subprocess.run(cmd, cwd=wav2lip_dir, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Wav2Lip failed: {res.stderr}")
    print("✅ Wav2Lip lip-sync complete!")

# ==============================================================================
# STEP 6: RENDER CLEAN FINAL REEL (NO TEXT BOXES)
# ==============================================================================
def render_clean_reel():
    print("5️⃣ Exporting clean talking-head video for Facebook Reels...")
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip

    target_w, target_h = 1080, 1920
    video_clip = VideoFileClip(VIDEO_LIPSYNC).resized((target_w, target_h))
    audio_clip = AudioFileClip(VOICE_AUDIO_MP3)
    
    final = video_clip.with_audio(audio_clip)
    
    final.write_videofile(
        FINAL_REEL, 
        fps=25, 
        codec="libx264", 
        audio_codec="aac",
        preset="ultrafast",
        logger=None
    )
    
    video_clip.close()
    audio_clip.close()
    final.close()
    print("✅ Clean Reel exported successfully!")

# ==============================================================================
# STEP 7: PUBLISH TO FACEBOOK
# ==============================================================================
def publish_to_facebook(content):
    print("6️⃣ Uploading clean Reel to Facebook Page...")
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
    
    # Put the question and options neatly in the post description so Facebook's caption engine handles it cleanly
    description = (
        f"🎯 {content['topic'].upper()}\n\n"
        f"❓ {content['question']}\n\n"
        f"{content['option_a']}\n"
        f"{content['option_b']}\n"
        f"{content['option_c']}\n"
        f"{content['option_d']}\n\n"
        f"💡 Drop your answer in the comments! #PMP #ProjectManagement #Agile #PMPExam"
    )
    
    payload = {
        "description": description,
        "access_token": FB_ACCESS_TOKEN,
        "published": "true"
    }
    
    with open(FINAL_REEL, "rb") as video_file:
        files = {"source": video_file}
        res = requests.post(url, data=payload, files=files, timeout=180)
        
    res_data = res.json()
    if "error" in res_data:
        raise RuntimeError(f"Facebook Graph API Error:\n{json.dumps(res_data['error'], indent=2)}")
        
    print(f"🎉 Successfully published clean Reel to Facebook! Video ID: {res_data['id']}")

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    try:
        validate_environment()
        content = get_daily_pmp_content()
        generate_character_image()
        
        asyncio.run(generate_neural_voice(content["spoken_script"]))
        animate_character_mouth()
        render_clean_reel()
        publish_to_facebook(content)
        
        print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        print("\n" + "="*60)
        print("🔥 FATAL ERROR CAUGHT IN PIPELINE 🔥")
        print("="*60)
        traceback.print_exc()
        print("="*60)
        sys.exit(1)
