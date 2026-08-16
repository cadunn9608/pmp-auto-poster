import os
import json
import time
import subprocess
import requests
import glob

# ==============================================================================
# CRITICAL PERFORMANCE PATCHES FOR GITHUB ACTIONS CPU
# ==============================================================================
os.environ["TORCH_FORCE_WEIGHTS_ONLY_LOAD"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

from google import genai
from gtts import gTTS
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

# ==============================================================================
# CONFIGURATION & ABSOLUTE PATH SETUP
# ==============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

TARGET_FILENAME = "andrew_petey_anchor_clean.mp4"
POSSIBLE_PATHS = [
    os.path.join(ROOT_DIR, TARGET_FILENAME),
    os.path.join(ROOT_DIR, "assets", TARGET_FILENAME),
    os.path.join(ROOT_DIR, "media", TARGET_FILENAME)
]

if not any(os.path.exists(path) for path in POSSIBLE_PATHS):
    found_files = glob.glob(os.path.join(ROOT_DIR, "**", TARGET_FILENAME), recursive=True)
    POSSIBLE_PATHS.extend(found_files)

BASE_VIDEO = None
for path in POSSIBLE_PATHS:
    if os.path.exists(path):
        BASE_VIDEO = path
        break

if not BASE_VIDEO:
    raise FileNotFoundError(
        f"Could not find '{TARGET_FILENAME}'. "
        "Please ensure the video file is in the repository and named correctly."
    )

VOICE_AUDIO = os.path.join(ROOT_DIR, "speech.mp3")
SMALL_BASE_VIDEO = os.path.join(ROOT_DIR, "small_input_video.mp4")
LIPSYNC_VIDEO = os.path.join(ROOT_DIR, "animated_andrew_no_audio.mp4")
FINAL_REEL = os.path.join(ROOT_DIR, "daily_pmp_reel.mp4")

# ==============================================================================
# IMAGE/VIDEO PRE-PROCESSING (CPU OPTIMIZATION)
# ==============================================================================
def pre_process_assets():
    print(f"⚙️ Resizing {BASE_VIDEO} to 360x360 for CPU processing...")
    cmd = [
        "ffmpeg", "-y", 
        "-i", BASE_VIDEO, 
        "-vf", "scale=360:360:force_original_aspect_ratio=decrease,pad=360:360:(ow-iw)/2:(oh-ih)/2",
        "-r", "20",
        "-c:a", "copy",
        SMALL_BASE_VIDEO
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print("✅ Video resized successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg resizing failed: {e.stderr.decode()}")
        raise

# ==============================================================================
# STEP 1: GEMINI GENERATES PMP QUESTION + EXPRESSIVE SPOKEN SCRIPT
# ==============================================================================
def get_daily_pmp_content():
    print("1️⃣ Fetching PMP question and expressive script from Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Prompt explicitly instructs Gemini to use varied punctuation (?!...) 
    # to prevent a flat, monotone gTTS delivery.
    prompt = """
    Generate a PMP exam situational question and a lively, highly expressive spoken script for a 3D animated dog host named Andrew.
    Make sure the spoken script uses exclamation points, question marks, and natural pauses (using ellipses) so the speech engine sounds dynamic and engaging, not monotone!
    Output strictly as a valid JSON object with the following keys:
    {
        "topic": "Agile Stakeholder Engagement",
        "question": "A key stakeholder wants out-of-scope changes during a sprint...",
        "option_a": "A) Accept the changes",
        "option_b": "B) Direct them to the Product Owner",
        "option_c": "C) Escalate to the sponsor",
        "option_d": "D) Refuse the request",
        "correct_answer": "B) Direct them to the Product Owner",
        "explanation": "The Product Owner manages scope changes in Agile.",
        "spoken_script": "Hey team! Are you ready for today's tough PMP challenge? Listen closely... A key stakeholder demands out-of-scope changes right in the middle of an active sprint! What should you do? Is it Option A... accept them? Option B... direct them straight to the Product Owner? Option C... escalate? Or Option D... refuse completely? Think carefully!"
    }
    """
    
    text_models_to_try = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-3-flash-preview"
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
            
            raw_text = response.text.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0]
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0]
            
            parsed_json = json.loads(raw_text.strip())
            print(f"Successfully generated content using {model_name}!")
            return parsed_json
            
        except Exception as e:
            print(f"⚠️ Model {model_name} failed: {e}")
            last_exception = e
            
    raise Exception(f"All fallback models failed. Last error: {last_exception}")

# ==============================================================================
# STEP 2: VOICE GENERATION (gTTS)
# ==============================================================================
def generate_voiceover(text):
    print("2️⃣ Generating expressive audio track with gTTS...")
    tts = gTTS(text=text, lang='en', tld='com', slow=False)
    tts.save(VOICE_AUDIO)
    
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", VOICE_AUDIO]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        audio_duration = float(result.stdout.strip())
        print(f"Audio file saved successfully. Duration: {audio_duration:.2f}s")
        return audio_duration
    except ValueError:
        return 50.0

# ==============================================================================
# STEP 3: OPEN-SOURCE LIP-SYNCING (Wav2Lip)
# ==============================================================================
def sync_lip_movement():
    print("3️⃣ RUNNING WAV2LIP (CPU Optimized)...")
    if os.path.exists(LIPSYNC_VIDEO):
        os.remove(LIPSYNC_VIDEO)

    cmd = [
        "python", "inference.py",
        "--checkpoint_path", "checkpoints/wav2lip_gan.pth",
        "--face", SMALL_BASE_VIDEO,
        "--audio", VOICE_AUDIO,
        "--outfile", LIPSYNC_VIDEO,
        "--resize_factor", "1",
        "--face_det_batch_size", "4",
        "--nosmooth"
    ]
    
    work_dir = os.path.join(ROOT_DIR, "Wav2Lip")
    process_env = os.environ.copy()
    process_env["MKL_NUM_THREADS"] = "1"
    process_env["OMP_NUM_THREADS"] = "1"

    subprocess.run(cmd, cwd=work_dir, check=True, env=process_env)
    print("✅ Lip-sync animation complete!")

# ==============================================================================
# STEP 4: OVERLAY TEXT CARDS
# ==============================================================================
def render_final_reel(data, audio_duration):
    print("4️⃣ Overlaying text tiles onto animated Reel...")
    total_video_duration = audio_duration + 2.0 
    switch_time = audio_duration / 2.0 
    
    target_w, target_h = 1080, 1920
    bg_clip = VideoFileClip(LIPSYNC_VIDEO).resize(width=target_w)
    video_h = bg_clip.h
    y_video_pos = (target_h - video_h) // 2
    
    bg_clip = bg_clip.with_position(('center', y_video_pos))
    black_bg = ColorClip(size=(target_w, target_h), color=(0,0,0)).with_duration(total_video_duration)

    text_area_w = target_w - 100
    text_area_h = y_video_pos - 50

    q_text = (
        f"DAILY PMP PREP: {data['topic'].upper()}\n\n"
        f"{data['question']}\n\n"
        f"{data['option_a']}\n{data['option_b']}\n{data['option_c']}\n{data['option_d']}"
    )
    
    q_tile = TextClip(
        text=q_text,
        font_size=45,
        color='white',
        font='Arial-Bold',
        method='caption',
        size=(text_area_w, text_area_h)
    ).with_position(('center', 50)).with_start(0).with_duration(switch_time)

    a_text = (
        f"CORRECT ANSWER:\n{data['correct_answer']}\n\n"
        f"EXPLANATION:\n{data['explanation']}\n\n"
        f"👍 Like & Follow for Daily PMP Prep!"
    )
    
    a_tile = TextClip(
        text=a_text,
        font_size=50,
        color='yellow',
        font='Arial-Bold',
        method='caption',
        size=(text_area_w, text_area_h)
    ).with_position(('center', 50)).with_start(switch_time).with_duration(audio_duration - switch_time + 1.0)

    final = CompositeVideoClip([black_bg, bg_clip, q_tile, a_tile])
    final = final.with_duration(total_video_duration)

    print("Writing final video file...")
    try:
        final.write_videofile(
            FINAL_REEL, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast"
        )
        print("✅ Final animated Reel exported!")
    finally:
        bg_clip.close()
        final.close()

# ==============================================================================
# STEP 5: PUBLISH TO FACEBOOK
# ==============================================================================
def publish_to_facebook():
    print("5️⃣ Uploading Reel to Facebook Page...")
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
    
    payload = {
        "description": "Daily PMP Exam Practice Reel! 🐶 #PMP #ProjectManagement #Agile",
        "access_token": FB_ACCESS_TOKEN,
        "published": "true"
    }
    
    try:
        with open(FINAL_REEL, "rb") as video_file:
            files = {"source": video_file}
            res = requests.post(url, data=payload, files=files, timeout=60)
            print("Facebook Upload Response:", res.json())
    except Exception as e:
        print(f"❌ Facebook upload failed: {e}")

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    pre_process_assets()
    content = get_daily_pmp_content()
    audio_dur = generate_voiceover(content["spoken_script"])
    sync_lip_movement()
    render_final_reel(content, audio_dur)
    
    if FB_PAGE_ID and FB_ACCESS_TOKEN:
        publish_to_facebook()
    else:
        print("Facebook credentials not found. Video rendered locally only.")
