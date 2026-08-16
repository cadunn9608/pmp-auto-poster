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
VOICE_AUDIO_MP3 = os.path.join(ROOT_DIR, "speech_original.mp3")
VOICE_AUDIO_WAV = os.path.join(ROOT_DIR, "speech_90s.wav")
VIDEO_LIPSYNC = os.path.join(ROOT_DIR, "talking_head.mp4")
FINAL_REEL = os.path.join(ROOT_DIR, "daily_pmp_reel.mp4")

# Font path for GitHub Actions Ubuntu Runner
UBUNTU_FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

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
                    raw_text = raw_text.split("
