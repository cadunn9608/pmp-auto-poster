import os
import json
import time
import subprocess
import requests
from google import genai
from gtts import gTTS
from moviepy import VideoFileClip, TextClip, CompositeVideoClip

# ==============================================================================
# CONFIGURATION & ENVIRONMENT VARIABLES
# ==============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")

BASE_VIDEO = "andrew_petey_anchor_clean.mp4"  # 58-second clean base video
VOICE_AUDIO = "speech.mp3"
LIPSYNC_VIDEO = "animated_andrew.mp4"
FINAL_REEL = "daily_pmp_reel.mp4"

# ==============================================================================
# STEP 1: GEMINI GENERATES PMP QUESTION + VOICE SCRIPT (WITH FALLBACKS)
# ==============================================================================
def get_daily_pmp_content():
    print("1️⃣ Fetching PMP question and spoken script from Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = """
    Generate a PMP exam situational question and a lively spoken script for a 3D animated dog host named Andrew.
    Output strictly as valid JSON:
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
    
    # Priority list of models to try in order
    text_models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    
    last_exception = None
    for model_name in text_models_to_try:
        try:
            print(f"Attempting to generate content with model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            print(f"Successfully generated response using {model_name}!")
            return json.loads(response.text)
        except Exception as e:
            print(f"⚠️ Model {model_name} failed: {e}")
            last_exception = e
            
    # Raise exception if all fallback attempts fail
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
        "python", "Wav2Lip/inference.py",
        "--checkpoint_path", "Wav2Lip/checkpoints/wav2lip_gan.pth",
        "--face", BASE_VIDEO,
        "--audio", VOICE_AUDIO,
        "--outfile", LIPSYNC_VIDEO,
        "--resize_factor", "1"
    ]
    subprocess.run(cmd, check=True)
    print("Lip-sync animation complete!")

# ==============================================================================
# STEP 4: OVERLAY TEXT CARDS OVER ANIMATED VIDEO
# ==============================================================================
def render_final_reel(data):
    print("4️⃣ Overlaying text tiles onto animated Reel...")
    bg_clip = VideoFileClip(LIPSYNC_VIDEO)
    bg_clip = bg_clip.subclipped(0, 58) if hasattr(bg_clip, 'subclipped') else bg_clip.subclip(0, 58)
    
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
# STEP 5: PUBLISH TO FACEBOOK (FREE GRAPH API)
# ==============================================================================
def publish_to_facebook():
    print("5️⃣ Uploading Reel to Facebook Page...")
    init_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/video_reels"
    init_params = {"upload_phase": "start", "access_token": FB_ACCESS_TOKEN}
    init_res = requests.post(init_url, data=init_params).json()
    
    video_id = init_res.get("video_id")
    upload_url = init_res.get("upload_url")

    with open(FINAL_REEL, "rb") as f:
        headers = {"Authorization": f"OAuth {FB_ACCESS_TOKEN}", "file_offset": "0"}
        requests.post(upload_url, headers=headers, data=f)

    finish_params = {
        "upload_phase": "finish",
        "access_token": FB_ACCESS_TOKEN,
        "video_id": video_id,
        "video_state": "PUBLISHED",
        "description": "Daily PMP Exam Practice Reel! 🐶 #PMP #ProjectManagement #Agile"
    }
    res = requests.post(init_url, data=finish_params).json()
    print("Facebook Publish Status:", res)

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
