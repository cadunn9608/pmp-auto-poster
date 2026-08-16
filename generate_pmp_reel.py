import os
import json
import time
import subprocess
import random
import requests
import asyncio
import edge_tts
from google import genai
from PIL import Image
from io import BytesIO

# ==============================================================================
# CONFIGURATION & ABSOLUTE PATH SETUP
# ==============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

GENERATED_IMAGE = os.path.join(ROOT_DIR, "host_character.png")
VOICE_AUDIO = os.path.join(ROOT_DIR, "speech.mp3")
VIDEO_LIPSYNC = os.path.join(ROOT_DIR, "talking_head.mp4")
FINAL_REEL = os.path.join(ROOT_DIR, "daily_pmp_reel.mp4")

# ==============================================================================
# STEP 1: RANDOMIZED PMBOK TOPIC POOL (COMPLETE COVERAGE)
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
# STEP 3: GEMINI GENERATES PMP CONTENT (WITH ROBUST MODEL FALLBACK)
# ==============================================================================
def get_daily_pmp_content():
    print("1️⃣ Fetching diverse PMP question and expressive script from Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    selected_topic = random.choice(pmp_reel_topics)
    
    prompt = (
        f"Create a rigorous, situational PMP exam practice question specifically focused on: {selected_topic}, "
        "alongside a lively, highly expressive spoken script for the 3D animated animal host to present in a short-form video. "
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
        '    "spoken_script": "Hey team! Are you ready for today\'s PMP challenge? Listen closely... [Question introduction]? Is it Option A... [detail]? Option B... [detail]? Think carefully!"\n'
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
                print(f"Attempting content generation with {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
                )
                raw_text = response.text.strip()
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0]
                elif "```" in raw_text:
                    raw_text = raw_text.split("```")[1].split("```")[0]
                return json.loads(raw_text.strip())
            except Exception as e:
                last_exception = e
                if "503" in str(e):
                    time.sleep(10)
                continue
        time.sleep(attempt * 15)
            
    raise Exception(f"All models and retries failed. Last error: {last_exception}")

# ==============================================================================
# STEP 4: GENERATE CHARACTER PORTRAIT NATIVELY VIA GEMINI
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
            response = client.models.generate_content(model=img_model, contents=image_prompt)
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.inline_data and part.inline_data.data:
                        image_bytes = part.inline_data.data
                        break
                if image_bytes: break
            if image_bytes: break
        except Exception:
            continue
            
    if not image_bytes:
        raise Exception("All Gemini image generation models failed.")
        
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img.save(GENERATED_IMAGE)
    print("Character image successfully saved!")

# ==============================================================================
# STEP 5: REALISTIC NEURAL VOICE GENERATION (EDGE-TTS)
# ==============================================================================
async def generate_neural_voice(text):
    print("3️⃣ Generating realistic neural voice track with Edge-TTS...")
    # 'en-US-ChristopherNeural' is a highly realistic male voice. 
    # Alternatives: 'en-US-GuyNeural', 'en-US-EricNeural'
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(VOICE_AUDIO)

def get_audio_duration():
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", VOICE_AUDIO]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 45.0

# ==============================================================================
# STEP 6: ANIMATE MOUTH WITH WAV2LIP
# ==============================================================================
def animate_character_mouth():
    print("4️⃣ Animating character mouth with Wav2Lip (This step takes 20+ mins on CPU)...")
    
    wav2lip_script = os.path.join(ROOT_DIR, "Wav2Lip", "inference.py")
    checkpoint = os.path.join(ROOT_DIR, "Wav2Lip", "checkpoints", "wav2lip_gan.pth")
    
    # Run the Wav2Lip inference script as a subprocess
    cmd = [
        "python", wav2lip_script,
        "--checkpoint_path", checkpoint,
        "--face", GENERATED_IMAGE,
        "--audio", VOICE_AUDIO,
        "--outfile", VIDEO_LIPSYNC,
        "--nosmooth" # Helps prevent crashes on CPU runners
    ]
    
    # We use check=True so the workflow fails gracefully if the face detector can't find a face
    subprocess.run(cmd, check=True)
    print("✅ Wav2Lip animation complete!")

# ==============================================================================
# STEP 7: RENDER TALKING REEL (OVERLAY TEXT TILES)
# ==============================================================================
def render_final_reel(data, audio_duration):
    print("5️⃣ Assembling talking character Reel with text...")
    
    switch_time = audio_duration / 2.0 
    target_w, target_h = 1080, 1920

    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.video.VideoClip import TextClip, ColorClip
    from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

    # Load the lip-synced video created by Wav2Lip
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
        font='Arial-Bold',
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
        font='Arial-Bold',
        method='caption',
        size=(text_area_w, text_area_h)
    ).with_position(('center', 100)).with_start(switch_time).with_duration(audio_duration - switch_time + 1.0)
    
    a_box = ColorClip(size=(text_area_w, text_area_h + 50), color=(15, 23, 42)).with_opacity(0.85).with_position(('center', 80)).with_start(switch_time).with_duration(audio_duration - switch_time + 1.0)

    final = CompositeVideoClip([video_clip, q_box, q_text_clip, a_box, a_text_clip])
    
    print("Writing final video file...")
    try:
        final.write_videofile(
            FINAL_REEL, 
            fps=25, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast"
        )
        print("✅ Final talking character Reel exported!")
    finally:
        video_clip.close()
        final.close()

# ==============================================================================
# STEP 8: PUBLISH TO FACEBOOK
# ==============================================================================
def publish_to_facebook():
    print("6️⃣ Uploading Reel to Facebook Page...")
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
    payload = {
        "description": "Daily PMP Exam Practice Reel! 🐶 #PMP #ProjectManagement #Agile",
        "access_token": FB_ACCESS_TOKEN,
        "published": "true"
    }
    try:
        with open(FINAL_REEL, "rb") as video_file:
            files = {"source": video_file}
            res = requests.post(url, data=payload, files=files, timeout=120)
            print("Facebook Upload Response:", res.json())
    except Exception as e:
        print(f"❌ Facebook upload failed: {e}")

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    content = get_daily_pmp_content()
    generate_character_image()
    
    # Run the async Edge-TTS function
    asyncio.run(generate_neural_voice(content["spoken_script"]))
    audio_dur = get_audio_duration()
    
    animate_character_mouth()
    render_final_reel(content, audio_dur)
    
    if FB_PAGE_ID and FB_ACCESS_TOKEN:
        publish_to_facebook()
    else:
        print("Facebook credentials not found. Video rendered locally only.")
