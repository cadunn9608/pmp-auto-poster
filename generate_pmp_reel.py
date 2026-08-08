import os
import json
import time
import subprocess
import requests

# Bypass PyTorch 2.6+ unpickling restriction for legacy model checkpoints
os.environ["TORCH_FORCE_WEIGHTS_ONLY_LOAD"] = "0"

from google import genai
from gtts import gTTS
from moviepy import VideoFileClip, TextClip, CompositeVideoClip

# ==============================================================================
# CONFIGURATION & ABSOLUTE PATH SETUP
# ==============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")

# Determine base working directory dynamically
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Flexible file lookup for base video asset
TARGET_FILENAME = "andrew_petey_anchor_clean.mp4"
POSSIBLE_PATHS = [
    os.path.join(ROOT_DIR, TARGET_FILENAME),
    os.path.join(ROOT_DIR, "assets", TARGET_FILENAME),
    os.path.join(ROOT_DIR, "media", TARGET_FILENAME)
]

if os.path.exists(ROOT_DIR):
    for f in os.listdir(ROOT_DIR):
        if f.lower() == TARGET_FILENAME.lower():
            POSSIBLE_PATHS.insert(0, os.path.join(ROOT_DIR, f))

BASE_VIDEO = None
for path in POSSIBLE_PATHS:
    if os.path.exists(path):
        BASE_VIDEO = path
        break

if not BASE_VIDEO:
    raise FileNotFoundError(
        f"Could not find '{TARGET_FILENAME}' in {ROOT_DIR}. "
        "Please ensure the video file is committed to your repository!"
    )

VOICE_AUDIO = os.path.join(ROOT_DIR, "speech.mp3")
LIPSYNC_VIDEO = os.path.join(ROOT_DIR, "animated_andrew.mp4")
FINAL_REEL = os.path.join(ROOT_DIR, "daily_pmp_reel.mp4")

# ==============================================================================
# STEP 1: GEMINI GENERATES PMP QUESTION + VOICE SCRIPT (GEMINI 3 ENGINE)
# ==============================================================================
def get_daily_pmp_content():
    print("1️⃣ Fetching PMP question and spoken script from Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = """
    Generate a PMP exam situational question and a lively spoken script for a 3D animated dog host named Andrew.
    Output strictly as a valid JSON object with the following keys:
    {
        "topic": "Agile Stakeholder Engagement",
        "question": "A key stakeholder wants out-of-scope changes during a sprint...",
        "option_a": "A) Accept the changes",
        "option_b": "B) Direct them to the Product Owner",
        "option_c": "C) Escalate to the sponsor",
        "option_d": "D) Refuse the request",
        "correct_answer": "B) Direct them to the Product Owner",
        "explanation": "In Agile, the Product Owner owns the product backlog and evaluates scope changes.",
        "spoken_script": "Hey team! Here is your daily PMP practice question. A key stakeholder asks for out-of-scope changes during an active sprint. What should you do? Option A, accept them. Option B, direct them to the Product Owner. Option C, escalate. Or Option D, refuse. Think about it!"
    }
    """
    
    # Strictly Gemini 3 models list
    text_models_to_try = [
        "gemini-3.5-flash",
        "gemini-3.1-flash",
        "gemini-3.6-flash",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite"
    ]
    
    last_exception = None
    for model_name in text_models_to_try:
        try:
            print(f"Attempting content generation with model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            
            # Sanitize output string
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            cleaned_text = raw_text.strip()
            
            parsed_json = json.loads(cleaned_text)
            print(f"Successfully generated and parsed response using {model_name}!")
            return parsed_json
            
        except Exception as e:
            print(f"⚠️ Model {model_name} failed: {e}")
            last_exception = e
            
    raise Exception(f"All fallback models failed. Last error: {last_exception}")

# ==============================================================================
# STEP 2: FREE VOICE GENERATION (gTTS)
# ==============================================================================
def generate_voiceover(text):
    print("2️⃣ Generating free audio track with gTTS...")
    tts = gTTS(text=text, lang='en', tld='com', slow=False)
    tts.save(VOICE_AUDIO)
    print("Audio file saved successfully.")

# ==============================================================================
# STEP 3: OPEN-SOURCE LIP-SYNCING (Wav2Lip)
# ==============================================================================
def sync_lip_movement():
    print("3️⃣ Running Wav2Lip to animate Andrew's mouth to the audio...")
    
    cmd = [
        "python", "inference.py",
        "--checkpoint_path", "checkpoints/wav2lip_gan.pth",
        "--face", BASE_VIDEO,
        "--audio", VOICE_AUDIO,
        "--outfile", LIPSYNC_VIDEO,
        "--resize_factor", "1"
    ]
    subprocess.run(cmd, cwd=os.path.join(ROOT_DIR, "Wav2Lip"), check=True)
    print("Lip-sync animation complete!")

# ==============================================================================
# STEP 4: OVERLAY TEXT CARDS OVER ANIMATED VIDEO
# ==============================================================================
def render_final_reel(data):
    print("4️⃣ Overlaying text tiles onto animated Reel...")
    bg_clip = VideoFileClip(LIPSYNC_VIDEO)
    
    # Question Overlay (0s - 30s)
    q_text = (
        f"DAILY PMP PREP: {data['topic'].upper()}\n\n"
        f"Q: {data['question']}\n\n"
        f"{data['option_a']}\n{data['option_b']}\n{data['option_c']}\n{data['option_d']}"
    )
    q_tile = TextClip(
        text=q_text,
        font_size=24,
        color='white',
        bg_color='black',
        font='Arial-Bold',
        method='caption',
        size=(620, 750),
        text_align='center'
    ).with_position(('center', 100)).with_start(0).with_duration(30)

    # Answer Overlay (30s - 58s)
    a_text = (
        f"CORRECT ANSWER:\n{data['correct_answer']}\n\n"
        f"EXPLANATION:\n{data['explanation']}\n\n"
        f"👍 Like & Follow for Daily PMP Prep!"
    )
    a_tile = TextClip(
        text=a_text,
        font_size=26,
        color='yellow',
        bg_color='black',
        font='Arial-Bold',
        method='caption',
        size=(620, 650),
        text_align='center'
    ).with_position(('center', 150)).with_start(30).with_duration(28)

    final = CompositeVideoClip([bg_clip, q_tile, a_tile])
    final.write_videofile(FINAL_REEL, fps=30, codec="libx264", audio_codec="aac")
    print("Final 58-second animated Reel exported!")

# ==============================================================================
# STEP 5: PUBLISH TO FACEBOOK (DIRECT PAGE VIDEO UPLOAD)
# ==============================================================================
def publish_to_facebook():
    print("5️⃣ Uploading Reel to Facebook Page...")
    url = f"[https://graph.facebook.com/v19.0/](https://graph.facebook.com/v19.0/){FB_PAGE_ID}/videos"
    
    payload = {
        "description": "Daily PMP Exam Practice Reel! 🐶 #PMP #ProjectManagement #Agile",
        "access_token": FB_ACCESS_TOKEN
    }
    
    with open(FINAL_REEL, "rb") as video_file:
        files = {
            "source": video_file
        }
        res = requests.post(url, data=payload, files=files)
        
    print("Facebook Upload Response:", res.json())

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    content = get_daily_pmp_content()
    generate_voiceover(content["spoken_script"])
    sync_lip_movement()
    render_final_reel(content)
    
    if FB_PAGE_ID and FB_ACCESS_TOKEN:
        publish_to_facebook()
    else:
        print("Facebook credentials not found. Video rendered locally only.")
