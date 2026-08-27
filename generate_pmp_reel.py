import os
import sys
import subprocess
import asyncio
import requests
import json
import re
from PIL import Image
from io import BytesIO

# --- MOVIEPY COMPATIBILITY LAYER ---
try:
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip
except ImportError:
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.video.VideoClip import TextClip, ColorClip
    from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip

from google import genai
from google.genai import types
import edge_tts

# ==========================================
# PIPELINE CONFIGURATION & ENV VALIDATION
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FACEBOOK_ACCESS_TOKEN")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing.")

client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# MOVIEPY V1/V2 HELPER FUNCTIONS
# ==========================================
def resize_clip(clip, **kwargs):
    if hasattr(clip, "resized"):
        return clip.resized(**kwargs)
    return clip.resize(**kwargs)

def set_clip_position(clip, pos):
    if hasattr(clip, "with_position"):
        return clip.with_position(pos)
    return clip.set_position(pos)

def set_clip_duration(clip, duration):
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    return clip.set_duration(duration)

# ==========================================
# WAV2LIP COMPATIBILITY PATCHES
# ==========================================
def patch_wav2lip_files():
    """Patches Wav2Lip scripts for librosa, OpenCV fourcc, and temp folder compatibility."""
    wav2lip_dir = os.path.abspath("Wav2Lip")
    os.makedirs(os.path.join(wav2lip_dir, "temp"), exist_ok=True)

    audio_py = os.path.join(wav2lip_dir, "audio.py")
    if os.path.exists(audio_py):
        with open(audio_py, "r") as f:
            content = f.read()
        if "librosa.filters.mel(hp.sample_rate, hp.n_fft," in content:
            content = content.replace(
                "librosa.filters.mel(hp.sample_rate, hp.n_fft,",
                "librosa.filters.mel(sr=hp.sample_rate, n_fft=hp.n_fft,"
            )
            with open(audio_py, "w") as f:
                f.write(content)
            print("🔧 Patched Wav2Lip/audio.py for modern librosa compatibility.")

    inference_py = os.path.join(wav2lip_dir, "inference.py")
    if os.path.exists(inference_py):
        with open(inference_py, "r") as f:
            content = f.read()
        
        modified = False
        if "os.makedirs('temp', exist_ok=True)" not in content:
            content = "import os\nos.makedirs('temp', exist_ok=True)\n" + content
            modified = True
            
        if "cv2.VideoWriter_fourcc(*'DIVX')" in content:
            content = content.replace("cv2.VideoWriter_fourcc(*'DIVX')", "cv2.VideoWriter_fourcc(*'MJPG')")
            modified = True

        if modified:
            with open(inference_py, "w") as f:
                f.write(content)
            print("🔧 Patched Wav2Lip/inference.py for temp folder & OpenCV MJPG video codec.")

# ==========================================
# STEP 1: GEMINI TEXT GENERATION
# ==========================================
def generate_pmp_content():
    print("1️⃣ Fetching full-length PMP question and script from Gemini...")
    
    prompt = """
    Create a realistic, high-quality PMP (Project Management Professional) exam scenario question.
    Format your output strictly as a JSON object with the following keys:
    {
        "question": "The scenario question text here...",
        "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
        "correct_answer": "A) Option 1",
        "narration": "Natural, engaging spoken narration for a 30-45 second video reel. Start with 'Here is your daily PMP exam question.', state the scenario clearly, present the options, give a brief 2-second pause cue, and explain the correct choice based on the PMBOK guide."
    }
    Return ONLY valid JSON.
    """
    
    candidate_models = ["gemini-3.6-flash", "gemini-2.5-flash"]
    
    for model_name in candidate_models:
        try:
            print(f"🔄 Attempting text generation with model '{model_name}'...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(response.text)
            print(f"✅ Content generated successfully using '{model_name}'.")
            return data
        except Exception as e:
            print(f"⚠️ Generation failed with model '{model_name}': {e}")
            
    print("⚠️ Returning fallback static PMP question data...")
    return {
        "question": "A project manager is facing scope creep during execution due to unapproved stakeholder requests. What should the project manager do FIRST?",
        "options": [
            "A) Implement the changes immediately to satisfy stakeholders",
            "B) Evaluate the impact of the changes using the Perform Integrated Change Control process",
            "C) Reject all incoming requests",
            "D) Escalate the issue directly to the project sponsor"
        ],
        "correct_answer": "B) Evaluate the impact of the changes using the Perform Integrated Change Control process",
        "narration": "Here is your daily PMP practice question! A project manager is facing scope creep during execution due to unapproved stakeholder requests. What should the project manager do first? The correct answer is B! Always process changes through the Perform Integrated Change Control process before updating baseline scope."
    }

# ==========================================
# STEP 2: CHARACTER PORTRAIT GENERATION
# ==========================================
def generate_character_image(prompt_text="A professional project manager host speaking into a studio microphone, portrait photo, centered face, high resolution"):
    print("2️⃣ Preparing character portrait...")
    output_path = os.path.abspath("character.png")

    try:
        print("🔄 Generating portrait via Pollinations AI...")
        encoded_prompt = requests.utils.quote(prompt_text)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=768&nologo=true"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            img.save(output_path)
            print(f"✅ Character portrait generated and saved to '{output_path}'.")
            return output_path
    except Exception as e:
        print(f"⚠️ Pollinations AI generation failed: {e}")

    try:
        print("🔄 Downloading fallback default avatar...")
        fallback_url = "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=800&q=80"
        resp = requests.get(fallback_url, timeout=15)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            img.save(output_path)
            print(f"✅ Default character portrait saved to '{output_path}'.")
            return output_path
    except Exception as e:
        print(f"⚠️ Default avatar download failed: {e}")

    if os.path.exists(output_path):
        print(f"✅ Using pre-existing '{output_path}'.")
        return output_path

    raise RuntimeError("Could not generate or download a character portrait.")

# ==========================================
# STEP 3: TEXT-TO-SPEECH (EDGE-TTS)
# ==========================================
async def generate_tts_async(text, output_audio_path):
    voice = "en-US-ChristopherNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_audio_path)

def generate_audio(narration_text):
    print("3️⃣ Generating natural voice narration audio...")
    mp3_path = os.path.abspath("narration.mp3")
    wav_path = os.path.abspath("narration.wav")
    
    asyncio.run(generate_tts_async(narration_text, mp3_path))
    
    cmd = ["ffmpeg", "-y", "-i", mp3_path, "-ac", "1", "-ar", "16000", wav_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"✅ Audio generated and converted to '{wav_path}'.")
    return wav_path

# ==========================================
# STEP 4: WAV2LIP LIP-SYNC GENERATION
# ==========================================
def run_wav2lip(image_path="character.png", audio_path="narration.wav"):
    print("4️⃣ Running Wav2Lip lip-sync generation...")
    
    output_video = os.path.abspath("wav2lip_output.mp4")
    abs_image_path = os.path.abspath(image_path)
    abs_audio_path = os.path.abspath(audio_path)
    
    patch_wav2lip_files()

    wav2lip_dir = os.path.abspath("Wav2Lip")
    if wav2lip_dir not in sys.path:
        sys.path.append(wav2lip_dir)

    checkpoint = os.path.join(wav2lip_dir, "checkpoints", "wav2lip_gan.pth")
    if not os.path.exists(checkpoint):
        checkpoint = os.path.join(wav2lip_dir, "checkpoints", "wav2lip.pth")

    inference_script = os.path.join(wav2lip_dir, "inference.py")

    cmd = [
        sys.executable,
        inference_script,
        "--checkpoint_path", checkpoint,
        "--face", abs_image_path,
        "--audio", abs_audio_path,
        "--outfile", output_video,
        "--nosmooth",
        "--resize_factor", "1"
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=wav2lip_dir, capture_output=True, text=True)
    
    if result.returncode != 0 or not os.path.exists(output_video) or os.path.getsize(output_video) == 0:
        print(f"❌ Wav2Lip STDOUT:\n{result.stdout}")
        print(f"❌ Wav2Lip STDERR:\n{result.stderr}")
        raise RuntimeError(f"Wav2Lip failed to create output file at '{output_video}'. Exit code: {result.returncode}")
        
    print(f"✅ Wav2Lip video generated: '{output_video}'.")
    return output_video

# ==========================================
# STEP 5: COMPOSITE FINAL 9:16 REEL
# ==========================================
def create_final_reel(wav2lip_video_path, pmp_data):
    print("5️⃣ Building final 9:16 vertical Reel...")
    output_reel = os.path.abspath("final_pmp_reel.mp4")
    
    avatar_clip = VideoFileClip(wav2lip_video_path)
    
    target_w, target_h = 1080, 1920
    avatar_resized = resize_clip(avatar_clip, width=target_w)
    avatar_positioned = set_clip_position(avatar_resized, ("center", 150))
    
    background = set_clip_duration(ColorClip(size=(target_w, target_h), color=(15, 23, 42)), avatar_clip.duration)
    
    final_clip = CompositeVideoClip([background, avatar_positioned])
    final_clip.write_videofile(
        output_reel,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4
    )
    
    avatar_clip.close()
    final_clip.close()
    print(f"✅ Final Reel exported to '{output_reel}'.")
    return output_reel

# ==========================================
# STEP 6: PUBLISH TO FACEBOOK REELS
# ==========================================
def publish_to_facebook(video_path, caption):
    print("6️⃣ Uploading and publishing to Facebook Page Reels...")
    if not FB_PAGE_ID or not FB_ACCESS_TOKEN:
        print("⚠️ Facebook Page ID or Access Token missing. Skipping upload step.")
        return

    init_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/video_reels"
    init_payload = {
        "upload_phase": "start",
        "access_token": FB_ACCESS_TOKEN
    }
    
    init_res = requests.post(init_url, data=init_payload).json()
    if "video_id" not in init_res:
        print(f"❌ Failed to initialize FB Reel upload: {init_res}")
        return

    video_id = init_res["video_id"]
    upload_url = init_res["upload_url"]

    file_size = os.path.getsize(video_path)
    with open(video_path, "rb") as f:
        headers = {
            "Authorization": f"OAuth {FB_ACCESS_TOKEN}",
            "offset": "0",
            "file_size": str(file_size)
        }
        upload_res = requests.post(upload_url, headers=headers, data=f).json()

    finish_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/video_reels"
    finish_payload = {
        "upload_phase": "finish",
        "video_id": video_id,
        "video_state": "PUBLISHED",
        "description": caption,
        "access_token": FB_ACCESS_TOKEN
    }
    
    finish_res = requests.post(finish_url, data=finish_payload).json()
    if finish_res.get("success"):
        print(f"🎉 SUCCESS! Reel published successfully to Facebook Page! (Video ID: {video_id})")
    else:
        print(f"⚠️ FB Publishing response: {finish_res}")

# ==========================================
# MAIN EXECUTION PIPELINE
# ==========================================
if __name__ == "__main__":
    print("🚀 SCRIPT INITIATED: Full-Length Natural Audio & Precision Lip-Sync Pipeline...")
    print("✅ Environment variables validated.")
    
    try:
        pmp_data = generate_pmp_content()
        character_img = generate_character_image()
        audio_file = generate_audio(pmp_data["narration"])
        lip_synced_video = run_wav2lip(character_img, audio_file)
        final_reel_path = create_final_reel(lip_synced_video, pmp_data)
        
        caption = f"Daily PMP Exam Prep Question!\n\n{pmp_data['question']}\n\n#PMP #ProjectManagement #PMPPrep #CAPM #PMBOK"
        publish_to_facebook(final_reel_path, caption)
        
        print("✅ PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")

    except Exception as err:
        print("\n============================================================")
        print("🔥 FATAL ERROR CAUGHT IN PIPELINE 🔥")
        print("============================================================")
        raise err
