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

# Override print to ALWAYS flush the buffer immediately for GitHub Actions
import builtins
def print(*args, **kwargs):
    kwargs['flush'] = True
    builtins.print(*args, **kwargs)

print("🚀 SCRIPT INITIATED: Loading modules and configurations...")

# ==============================================================================
# CONFIGURATION & ABSOLUTE PATH SETUP
# ==============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

GENERATED_IMAGE = os.path.join(ROOT_DIR, "host_character.png")
VOICE_AUDIO_MP3 = os.path.join(ROOT_DIR, "speech_original.mp3")
VOICE_AUDIO_WAV = os.path.join(ROOT_DIR, "speech_90s.wav")
VIDEO_LIPSYNC = os.path.join(ROOT_DIR, "talking_head.mp4")
FINAL_REEL = os.path.join(ROOT_DIR, "daily_pmp_reel.mp4")

UBUNTU_FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# ==============================================================================
# ENVIRONMENT VALIDATION (FAIL FAST)
# ==============================================================================
def validate_environment():
    print("🔍 DEBUG: Validating environment variables...")
    missing = []
    if not GEMINI_API_KEY or not GEMINI_API_KEY.strip():
        missing.append("GEMINI_API_KEY")
    if not FB_PAGE_ID or not FB_PAGE_ID.strip():
        missing.append("FB_PAGE_ID")
    if not FB_ACCESS_TOKEN or not FB_ACCESS_TOKEN.strip():
        missing.append("FB_ACCESS_TOKEN")
        
    if missing:
        raise ValueError(f"❌ Critical environment variables missing:\n- " + "\n- ".join(missing))
    print("✅ DEBUG: All required environment variables are present.")

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

# ==============================================================================
# STEP 2: 20 DIVERSE CHARACTER & SETTING COMBINATIONS
# ==============================================================================
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
# STEP 3: GEMINI GENERATES PMP CONTENT (WITH FALLBACK)
# ==============================================================================
def get_daily_pmp_content():
    print("1️⃣ Fetching PMP question and script from Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    selected_topic = random.choice(pmp_reel_topics)
    
    prompt = (
        f"Create a rigorous, situational PMP exam practice question specifically focused on: {selected_topic}. "
        "Also write a highly detailed, lively, and expressive spoken script for the 3D animated animal host to read. "
        "The spoken script should be around 130 to 160 words so it takes about 60 to 75 seconds to speak. "
        "Use exclamation points, question marks, and natural pauses (using ellipses) in the spoken script so the voice engine sounds dynamic and engaging. "
        "IMPORTANT: Do not use any unescaped double quotes inside the string values. "
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
        '    "spoken_script": "Hey team! Are you ready for today\'s PMP challenge? [Detailed intro]... [Question read out]? Is it Option A... [detail]? Option B... [detail]? Think carefully, project managers!"\n'
        "}"
    )
    
    models_to_try = [
        "gemini-3.5-flash",
        "gemini-3.1-flash",
        "gemini-1.5-flash",
        "gemini-3-flash-preview",
        "gemini-3.6-flash",
        "gemini-1.5-pro",
        "gemini-3.1-flash-lite"
    ]
    
    last_exception = None
    for attempt in range(1, 4):
        for model_name in models_to_try:
            try:
                print(f"   DEBUG: Attempting text generation with {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
                )
                raw_text = response.text.strip()
                bt = chr(96) * 3
                if f"{bt}json" in raw_text:
                    raw_text = raw_text.split(f"{bt}json")[1].split(bt)[0]
                elif bt in raw_text:
                    raw_text = raw_text.split(bt)[1].split(bt)[0]
                    
                print(f"   ✅ DEBUG: Successfully got JSON from {model_name}")
                return json.loads(raw_text.strip())
            except Exception as e:
                last_exception = e
                print(f"   ⚠️ DEBUG: Failed with {model_name}: {e}")
                if "503" in str(e):
                    time.sleep(10)
                continue
        print(f"   DEBUG: Retrying text generation... (Attempt {attempt+1})")
        time.sleep(attempt * 15)
            
    raise RuntimeError(f"Failed to generate content after retries. Last error: {last_exception}")

# ==============================================================================
# STEP 4: GENERATE CHARACTER PORTRAIT
# ==============================================================================
def generate_character_image():
    print("2️⃣ Generating Pixar-style character portrait via Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    selected_combo = random.choice(character_settings_pool)
    
    image_prompt = (
        f"A striking vertical portrait shot in the distinct visual style of Pixar and Disney, "
        f"featuring {selected_combo}, "
        "facing the camera directly, talking and expressive, vibrant studio lighting, polished cinematic digital rendering, perfect vertical mobile composition."
    )
    
    image_models_to_try = ["gemini-3.1-flash-image", "gemini-3.1-flash-image-preview", "gemini-1.5-pro"]
    image_bytes = None
    
    for img_model in image_models_to_try:
        try:
            print(f"   DEBUG: Attempting image generation with {img_model}...")
            response = client.models.generate_content(model=img_model, contents=image_prompt)
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.inline_data and part.inline_data.data:
                        image_bytes = part.inline_data.data
                        break
                if image_bytes: break
            if image_bytes: 
                print(f"   ✅ DEBUG: Successfully generated image using {img_model}")
                break
        except Exception as e:
            print(f"   ⚠️ DEBUG: Image generation failed with {img_model}: {e}")
            continue
            
    if not image_bytes:
        raise RuntimeError("All Gemini image generation models failed.")
        
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img.save(GENERATED_IMAGE)
    print("✅ Character image successfully saved!")

# ==============================================================================
# STEP 5: REALISTIC NEURAL VOICE & AUDIO PADDING
# ==============================================================================
async def generate_neural_voice(text):
    print("3️⃣ Generating realistic neural voice track with Edge-TTS...")
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(VOICE_AUDIO_MP3)
    
    print("   Padding audio with silence to exactly 90 seconds (Facebook Reel max)...")
    cmd = [
        "ffmpeg", "-y", "-i", VOICE_AUDIO_MP3, 
        "-af", "apad", "-t", "90", 
        VOICE_AUDIO_WAV
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ DEBUG: FFmpeg stdout:\n{res.stdout}")
        print(f"❌ DEBUG: FFmpeg stderr:\n{res.stderr}")
        raise RuntimeError(f"FFmpeg audio padding failed: {res.stderr}")
    print("   ✅ DEBUG: Audio padded successfully.")

def get_original_speech_duration():
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", VOICE_AUDIO_MP3]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 45.0

# ==============================================================================
# STEP 6: ANIMATE MOUTH WITH WAV2LIP
# ==============================================================================
def animate_character_mouth():
    print("4️⃣ Animating character mouth with Wav2Lip (Processing 90s audio)...")
    wav2lip_dir = os.path.join(ROOT_DIR, "Wav2Lip")
    os.makedirs(os.path.join(wav2lip_dir, "temp"), exist_ok=True)
    
    checkpoint = os.path.join(wav2lip_dir, "checkpoints", "wav2lip_gan.pth")
    if not os.path.exists(checkpoint):
        raise FileNotFoundError(f"Missing Wav2Lip weights file: {checkpoint}")
    
    cmd = [
        "python", "inference.py", 
        "--checkpoint_path", checkpoint,
        "--face", GENERATED_IMAGE,
        "--audio", VOICE_AUDIO_WAV, 
        "--outfile", VIDEO_LIPSYNC,
        "--nosmooth" 
    ]
    
    print("   DEBUG: Running Wav2Lip subprocess...")
    # Capture output to print it cleanly in case of a crash
    res = subprocess.run(cmd, cwd=wav2lip_dir, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ DEBUG: Wav2Lip stdout:\n{res.stdout}")
        print(f"❌ DEBUG: Wav2Lip stderr:\n{res.stderr}")
        raise RuntimeError("Wav2Lip lip-syncing inference failed.")
    print("✅ Wav2Lip animation complete!")

# ==============================================================================
# STEP 7: RENDER FINAL REEL
# ==============================================================================
def render_final_reel(data, speech_duration):
    print("5️⃣ Assembling 90-second Reel with text overlays...")
    switch_time = speech_duration * 0.55 
    total_duration = 90.0 
    target_w, target_h = 1080, 1920

    print("   DEBUG: Loading MoviePy modules...")
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.video.VideoClip import TextClip, ColorClip
    from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

    video_clip = VideoFileClip(VIDEO_LIPSYNC).resized((target_w, target_h))
    
    text_area_w = target_w - 100
    text_area_h = 700

    q_text = (
        f"★ DAILY PMP PREP ★\n\n"
        f"{data['question']}\n\n"
        f"{data['option_a']}\n{data['option_b']}\n{data['option_c']}\n{data['option_d']}"
    )
    
    q_text_clip = TextClip(
        text=q_text,
        font_size=38,
        color='white',
        font=UBUNTU_FONT_PATH,
        method='caption',
        size=(text_area_w, text_area_h)
    ).with_position(('center', 100)).with_start(0).with_duration(switch_time)

    q_box = ColorClip(size=(text_area_w, text_area_h + 50), color=(15, 23, 42)).with_opacity(0.85).with_position(('center', 80)).with_start(0).with_duration(switch_time)

    a_text = (
        f"✅ CORRECT ANSWER:\n{data['correct_answer']}\n\n"
        f"🧠 MINDSET:\n{data['explanation']}\n\n"
        f"👍 Like & Follow for Daily PMP Prep!"
    )
    
    a_text_clip = TextClip(
        text=a_text,
        font_size=42,
        color='yellow',
        font=UBUNTU_FONT_PATH,
        method='caption',
        size=(text_area_w, text_area_h)
    ).with_position(('center', 100)).with_start(switch_time).with_duration(total_duration - switch_time)
    
    a_box = ColorClip(size=(text_area_w, text_area_h + 50), color=(15, 23, 42)).with_opacity(0.85).with_position(('center', 80)).with_start(switch_time).with_duration(total_duration - switch_time)

    final = CompositeVideoClip([video_clip, q_box, q_text_clip, a_box, a_text_clip])
    
    print("   DEBUG: Writing final video file. This might take a moment...")
    try:
        final.write_videofile(
            FINAL_REEL, 
            fps=25, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast",
            logger=None # Suppress the noisy progress bar from moviepy
        )
        print("✅ Final talking character Reel exported!")
    finally:
        video_clip.close()
        final.close()

# ==============================================================================
# STEP 8: PUBLISH TO FACEBOOK (STRICT ERROR REPORTING)
# ==============================================================================
def publish_to_facebook():
    print("6️⃣ Uploading Reel to Facebook Page...")
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
    payload = {
        "description": "Daily PMP Exam Practice Reel! 🐶 #PMP #ProjectManagement #Agile",
        "access_token": FB_ACCESS_TOKEN,
        "published": "true"
    }
    
    if not os.path.exists(FINAL_REEL):
        raise FileNotFoundError(f"Cannot upload! Video file not found at: {FINAL_REEL}")

    print("   DEBUG: Initiating POST request to Facebook Graph API...")
    with open(FINAL_REEL, "rb") as video_file:
        files = {"source": video_file}
        res = requests.post(url, data=payload, files=files, timeout=180)
        
    print(f"   DEBUG: Facebook API responded with status code: {res.status_code}")
    
    try:
        res_data = res.json()
    except Exception:
        res.raise_for_status()
        raise RuntimeError(f"Non-JSON response received from Facebook: {res.text}")

    if "error" in res_data:
        raise RuntimeError(f"Facebook Graph API Error:\n{json.dumps(res_data['error'], indent=2)}")
        
    if "id" not in res_data:
        raise RuntimeError(f"Unexpected response from Facebook: {res_data}")

    print(f"🎉 Successfully published Reel to Facebook! Video ID: {res_data['id']}")

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    try:
        validate_environment()
        
        content = get_daily_pmp_content()
        generate_character_image()
        
        asyncio.run(generate_neural_voice(content["spoken_script"]))
        speech_dur = get_original_speech_duration()
        
        animate_character_mouth()
        render_final_reel(content, speech_dur)
        publish_to_facebook()
        
        print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        print("\n" + "="*60)
        print("🔥 FATAL ERROR CAUGHT IN PIPELINE 🔥")
        print("="*60)
        traceback.print_exc()
        print("="*60)
        sys.exit(1)
