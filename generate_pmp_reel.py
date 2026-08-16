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
# STEP 2: 20
