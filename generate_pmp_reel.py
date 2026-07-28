import os
import json
import time
import requests
from google import genai

# MoviePy v2.0+ updated imports
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip, CompositeVideoClip

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
        model="gemini-2.5-flash",
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
    bg_clip = VideoFileClip(BACKGROUND_VIDEO_PATH).subclip(0, 58)
    
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
    
    q_tile = (
        TextClip(
            text=question_text,
            font_size=24,
            color='white',
            bg_color='black',
            font='Arial-Bold',
            method='caption',
            size=(620, 800),
            text_align='center'
        )
        .with_position(('center', 120))
        .with_start(0)
        .with_duration(30)  # Full 30 seconds for reading
    )
    
    # --- TILE 2: ANSWER & EXPLANATION CARD (30s to 58s) ---
    answer_text = (
        f"CORRECT ANSWER: {data['correct_answer']}\n\n"
        f"EXPLANATION:\n{data['explanation']}\n\n"
        f"👍 Like, Share & Follow for Daily PMP Practice!"
    )
    
    a_tile = (
        TextClip(
            text=answer_text,
            font_size=26,
            color='yellow',
            bg_color='black',
            font='Arial-Bold',
            method='caption',
            size=(620, 700),
            text_
