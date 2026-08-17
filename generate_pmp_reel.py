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

import builtins
def print(*args, **kwargs):
    kwargs['flush'] = True
    builtins.print(*args, **kwargs)

print("🚀 SCRIPT INITIATED: Nano Banana Full-Motion Video Pipeline...")

# ==============================================================================
# CONFIGURATION & ABSOLUTE PATH SETUP
# ==============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

VOICE_AUDIO_MP3 = os.path.join(ROOT_DIR, "speech_original.mp3")
VIDEO_BACKGROUND = os.path.join(ROOT_DIR, "nano_banana_bg.mp4")
FINAL_REEL = os.path.join(ROOT_DIR, "daily_pmp_reel.mp4")

def validate_environment():
    missing = []
    if not GEMINI_API_KEY or not GEMINI_API_KEY.strip(): missing.append("GEMINI_API_KEY")
    if not FB_PAGE_ID or not FB_PAGE_ID.strip(): missing.append("FB_PAGE_ID")
    if not FB_ACCESS_TOKEN or not FB_ACCESS_TOKEN.strip(): missing.append("FB_ACCESS_TOKEN")
    if missing:
        raise ValueError(f"❌ Critical environment variables missing: {missing}")
    print("✅ Environment variables validated.")

pmp_reel_topics = [
    "agile team facilitation, servant leadership, and servant-leader mindset",
    "risk management, response strategies, and quantitative/qualitative risk analysis",
    "stakeholder engagement, communication planning, and managing expectations",
    "earned value management (EVM), schedule variance (SV), and cost variance (CV)",
    "change control procedures, integrated change control, and scope baseline management",
    "resource management, team charter, conflict resolution, and performance appraisals"
]

character_settings_pool = [
    "A 3D Pixar style golden retriever wearing a tiny project management hard hat.",
    "A 3D Pixar style friendly ginger cat wearing a sleek headset.",
    "A 3D Pixar style golden retriever puppy wearing tropical sunglasses."
]

# ==============================================================================
# STEP 1: CONTENT GENERATION
# ==============================================================================
def get_daily_pmp_content():
    print("1️⃣ Fetching full-length PMP question and script from Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    selected_topic = random.choice(pmp_reel_topics)
    
    prompt = (
        f"Create a rigorous, situational PMP exam practice question specifically focused on: {selected_topic}. "
        "Write a detailed, lively, and expressive spoken script for the animated host to read out loud. "
        "The spoken script should be comprehensive (around 130 to 160 words so it takes about 60 to 75 seconds to speak). "
        "Include the question breakdown, options, correct answer, and the PMP mindset explanation directly in the spoken script. "
        "Use exclamation points, question marks, and ellipses (...) where the host should pause for dramatic effect. "
        "Output strictly as a valid JSON object with these keys:\n"
        "{\n"
        f'    "topic": "{selected_topic}",\n'
        '    "question": "A situational PMP question description...",\n'
        '    "option_a": "A) First option text",\n'
        '    "option_b": "B) Second option text",\n'
        '    "option_c": "C) Third option text",\n'
        '    "option_d": "D) Fourth option text",\n'
        '    "correct_answer": "B) Second option text",\n'
        '    "explanation": "Concise PMP mindset explanation...",\n'
        '    "spoken_script": "Hey team! Are you ready for today\'s PMP challenge? Let\'s dive into a tough scenario about ' + selected_topic + '. Listen closely... [Read question outline]... Is it Option A? Option B? Option C? Or Option D? ... Let\'s look at the mindset. The correct answer is... [Explain why]! Keep crushing your PMP prep!"\n'
        "}"
    )
    
    models_to_try = ["gemini-3.5-flash", "gemini-3.1-flash", "gemini-1.5-flash"]
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
# STEP 2: NANO BANANA VIDEO GENERATION (FULL MOTION)
# ==============================================================================
def generate_nano_banana_video():
    print("2️⃣ Generating full-motion video via Nano Banana...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    base_character = random.choice(character_settings_pool)
    
    video_prompt = (
        f"Vertical 9:16 cinematic video. {base_character}. "
        "The character is highly animated, moving their head naturally, blinking their eyes, "
        "and making expressive hand gestures as if explaining a complex topic. "
        "A glowing, animated 3D lightbulb pops up and floats over their head. "
        "Bright studio lighting, Pixar/Disney 3D animation style, fluid motion."
    )
    
    try:
        # Requesting MP4 generation via Nano Banana / Gemini Video APIs
        response = client.models.generate_content(
            model="nano-banana-video", 
            contents=video_prompt
        )
        
        # Save the generated MP4 file directly
        video_bytes = response.candidates[0].content.parts[0].inline_data.data
        with open(VIDEO_BACKGROUND, "wb") as f:
            f.write(video_bytes)
            
        print("✅ Nano Banana dynamic video successfully generated!")
    except Exception as e:
        raise RuntimeError(f"Nano Banana video generation failed: {e}")

# ==============================================================================
# STEP 3: EXPRESSIVE AUDIO GENERATION
# ==============================================================================
async def generate_expressive_voice(text):
    print("3️⃣ Generating natural, expressive neural voice with SSML pauses...")
    ssml_text = (
        "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>"
        "<voice name='en-US-AndrewMultilingualNeural'>"
        "<prosody rate='+3%' pitch='+1Hz'>"
    )
    
    punctuated = text.replace("!", "! <break time='450ms'/>") \
                     .replace("?", "? <break time='550ms'/>") \
                     .replace(".", ". <break time='450ms'/>") \
                     .replace(",", ", <break time='250ms'/>") \
                     .replace("...", "<break time='650ms'/>")
                     
    ssml_text += punctuated + "</prosody></voice></speak>"
    
    communicate = edge_tts.Communicate(ssml_text, "en-US-AndrewMultilingualNeural")
    await communicate.save(VOICE_AUDIO_MP3)
    print("✅ Audio generated successfully!")

# ==============================================================================
# STEP 4: ASSEMBLE LOOPING REEL
# ==============================================================================
def assemble_final_reel():
    print("4️⃣ Merging Nano Banana visuals with natural Edge-TTS audio...")
    # Loop the animated Nano Banana video infinitely (-stream_loop -1)
    # until the audio track finishes (-shortest)
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", 
        "-i", VIDEO_BACKGROUND,
        "-i", VOICE_AUDIO_MP3,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest", 
        "-preset", "ultrafast",
        FINAL_REEL
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FFmpeg Error Output:\n{res.stderr}")
        raise RuntimeError(f"FFmpeg merging failed: {res.stderr}")
    print("✅ Full-length animated Reel exported successfully!")

# ==============================================================================
# STEP 5: PUBLISH TO FACEBOOK
# ==============================================================================
def publish_to_facebook(content):
    print("5️⃣ Uploading Reel to Facebook Page...")
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
    
    description = (
        f"🎯 {content['topic'].upper()}\n\n"
        f"❓ {content['question']}\n\n"
        f"{content['option_a']}\n"
        f"{content['option_b']}\n"
        f"{content['option_c']}\n"
        f"{content['option_d']}\n\n"
        f"💡 Correct Answer: {content['correct_answer']}\n"
        f"🧠 Mindset: {content['explanation']}\n\n"
        f"#PMP #ProjectManagement #Agile #PMPExam"
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
        
    print(f"🎉 Successfully published full-length Reel to Facebook! Video ID: {res_data['id']}")

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    try:
        validate_environment()
        content = get_daily_pmp_content()
        generate_nano_banana_video()
        
        asyncio.run(generate_expressive_voice(content["spoken_script"]))
        assemble_final_reel()
        publish_to_facebook(content)
        
        print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        print("\n" + "="*60)
        print("🔥 FATAL ERROR CAUGHT IN PIPELINE 🔥")
        print("="*60)
        traceback.print_exc()
        print("="*60)
        sys.exit(1)
