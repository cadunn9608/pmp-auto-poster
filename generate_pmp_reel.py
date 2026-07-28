import os
import json
import time
import requests
from google import genai

# MoviePy v2.0+ top-level imports
from moviepy import VideoFileClip, TextClip, CompositeVideoClip

# ==============================================================================
# CONFIGURATION & ENVIRONMENT VARIABLES
# ==============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")

BACKGROUND_VIDEO_PATH = "andrew_petey_anchor_clean.mp4" # Your clean 58s background video
OUTPUT_REEL_PATH = "daily_pmp_reel.mp4"

# ==============================================================================
# STEP 1: FETCH DAILY PMP QUESTION FROM GEMINI
# ==============================================================================
def get_daily_pmp_question():
    print("Fetching daily PMP question from Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = """
    Generate one highly realistic PMP exam situational question (Agile, Predictive, or Hybrid).
    Output strictly as a valid JSON object with the following keys:
    {
        "topic": "Agile Scope Change / Stakeholder Engagement",
        "question": "Clear, concise situational question...",
        "option_a": "A) First choice option",
        "option_b": "B) Second choice option",
        "option_c": "C) Third choice option",
        "option_d": "D) Fourth choice option",
        "correct_answer": "C) Third choice option",
        "explanation": "Brief breakdown explaining why this choice is correct according to the PMP ECO framework."
    }
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    
    return json.loads(response.text)

# ==============================================================================
# STEP 2: BUILD 58-SECOND REEL WITH MOVIEPY (TYPO-FREE TEXT OVERLAY)
# ==============================================================================
def render_reel(data):
    print("Rendering video with MoviePy text overlays...")
    
    # Load clean 58s background video (Andrew & Petey, no text/props)
    full_bg = VideoFileClip(BACKGROUND_VIDEO_PATH)
    bg_clip = full_bg.subclipped(0, 58) if hasattr(full_bg, 'subclipped') else full_bg.subclip(0, 58)
    
    # --- TILE 1: QUESTION CARD (0s to 30s) ---
    question_text = (
        f"DAILY PMP PREP: {data['topic'].upper()}\n\n"
        f"Q: {data['question']}\n\n"
        f"{data['option_a']}\n"
        f"{data['option_b']}\n"
        f"{data['option_c']}\n"
        f"{data['option_d']}\n\n"
        f"⏱️ Pause to read & comment your answer!"
    )
    
    q_tile = TextClip(
        text=question_text,
        font_size=24,
        color='white',
        bg_color='black',
        font='Arial-Bold',
        method='caption',
        size=(620, 800),
        text_align='center'
    ).with_position(('center', 120)).with_start(0).with_duration(30)
    
    # --- TILE 2: ANSWER & EXPLANATION CARD (30s to 58s) ---
    answer_text = (
        f"CORRECT ANSWER: {data['correct_answer']}\n\n"
        f"EXPLANATION:\n{data['explanation']}\n\n"
        f"👍 Like, Share & Follow for Daily PMP Practice!"
    )
    
    a_tile = TextClip(
        text=answer_text,
        font_size=26,
        color='yellow',
        bg_color='black',
        font='Arial-Bold',
        method='caption',
        size=(620, 700),
        text_align='center'
    ).with_position(('center', 160)).with_start(30).with_duration(28)
    
    # Composite and export final file
    final_reel = CompositeVideoClip([bg_clip, q_tile, a_tile])
    final_reel.write_videofile(
        OUTPUT_REEL_PATH,
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )
    print("Video successfully rendered and saved locally!")

# ==============================================================================
# STEP 3: PUBLISH REEL TO FACEBOOK VIA GRAPH API
# ==============================================================================
def publish_to_facebook_reel():
    print("Initiating Facebook Reel upload session...")
    
    # Stage 1: Initialize Upload Session
    init_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/video_reels"
    init_params = {
        "upload_phase": "start",
        "access_token": FB_ACCESS_TOKEN
    }
    init_res = requests.post(init_url, data=init_params).json()
    video_id = init_res.get("video_id")
    upload_url = init_res.get("upload_url")
    
    if not video_id or not upload_url:
        raise Exception(f"Failed to initialize Reel upload: {init_res}")
        
    print(f"Upload session initialized. Video ID: {video_id}")

    # Stage 2: Upload Video File Binary
    with open(OUTPUT_REEL_PATH, "rb") as video_file:
        headers = {
            "Authorization": f"OAuth {FB_ACCESS_TOKEN}",
            "file_offset": "0"
        }
        upload_res = requests.post(upload_url, headers=headers, data=video_file)
        print("Binary upload response:", upload_res.status_code)

    # Stage 3: Finish Upload & Publish
    finish_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/video_reels"
    finish_params = {
        "upload_phase": "finish",
        "access_token": FB_ACCESS_TOKEN,
        "video_id": video_id,
        "video_state": "PUBLISHED",
        "description": "Daily PMP Exam Practice Question! 🐶 Pass your exam with Andrew & Petey. #PMP #ProjectManagement #Agile #PMPExam"
    }
    
    finish_res = requests.post(finish_url, data=finish_params).json()
    print("Facebook Reels Publish Response:", finish_res)

# ==============================================================================
# MAIN EXECUTION FLOW
# ==============================================================================
if __name__ == "__main__":
    pmp_data = get_daily_pmp_question()
    render_reel(pmp_data)
    
    if FB_PAGE_ID and FB_ACCESS_TOKEN:
        publish_to_facebook_reel()
    else:
        print("Facebook credentials not found. Video rendered locally only.")
