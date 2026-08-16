import os
import json
import time
import subprocess
import requests
import torch
from PIL import Image
# Use diffusers to generate the host image instead of relying on a base video
from diffusers import StableDiffusionPipeline
from google import genai
from gtts import gTTS
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip, ColorClip, ImageClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

# ==============================================================================
# CONFIGURATION & PATH SETUP
# ==============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
HUGGINGFACE_TOKEN = os.environ.get("HUGGINGFACE_TOKEN") # You need to add this to secrets
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Output paths
GENERATED_IMAGE = os.path.join(ROOT_DIR, "host_image.png")
VOICE_AUDIO = os.path.join(ROOT_DIR, "speech.mp3")
# This will be the video of the image zooming, without audio yet
VIDEO_NO_AUDIO = os.path.join(ROOT_DIR, "zooming_image_no_audio.mp4")
FINAL_REEL = os.path.join(ROOT_DIR, "daily_pmp_reel.mp4")

# ==============================================================================
# STEP 1: GENERATE HOST IMAGE (Stable Diffusion)
# ==============================================================================
def generate_host_image():
    print("1️⃣ Generating host image using Stable Diffusion...")
    # We generate an image suitable for a charismatic PMP host
    prompt = "Pixar style 3D render of a charismatic golden retriever wearing a tiny project management hard hat and holding a clipboard, studio lighting, solid blue background, high quality"
    
    try:
        # Use a fast, lighter model for CPU execution
        model_id = "runwayml/stable-diffusion-v1-5"
        # Force CPU execution. This will still be slow on GitHub Actions.
        pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float32)
        pipe = pipe.to("cpu") 
        
        # Optimize for speed (fewer inference steps)
        image = pipe(prompt, num_inference_steps=20).images[0]
        image.save(GENERATED_IMAGE)
        print(f"✅ Host image saved to {GENERATED_IMAGE}")
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        # Fallback: create a blank red image so the script continues (for testing)
        img = Image.new('RGB', (512, 512), color='red')
        img.save(GENERATED_IMAGE)

# ==============================================================================
# STEP 2: GEMINI GENERATES PMP CONTENT
# ==============================================================================
def get_daily_pmp_content():
    print("2️⃣ Fetching PMP question and expressive script from Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = """
    Generate a PMP exam situational question and a lively, highly expressive spoken script for a charismatic 3D animated dog host.
    Use exclamation points, question marks, and natural pauses (using ellipses) so the speech engine sounds dynamic and engaging.
    Output strictly as a valid JSON object with the following keys:
    {
        "topic": "Risk Management",
        "question": "A project team discovers a new risk that could delay the project by two weeks...",
        "option_a": "A) Update the risk register",
        "option_b": "B) Crash the schedule immediately",
        "option_c": "C) Inform the sponsor first",
        "option_d": "D) Perform qualitative risk analysis",
        "correct_answer": "A) Update the risk register",
        "explanation": "The first step when identifying a new risk is to document it in the risk register.",
        "spoken_script": "Alright PMP hopefuls, here is a tricky one! A new risk is discovered that might cause a two-week delay. What is the immediate first action you must take? Option A... update the risk register. Option B... crash the schedule. Option C... inform the sponsor. Or Option D... perform qualitative risk analysis. Think like a Project Manager!"
    }
    """
    
    # Fallback models list
    text_models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-3-flash-preview"]
    
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
            return json.loads(raw_text.strip())
        except Exception as e:
            last_exception = e
    raise Exception(f"All fallback models failed. Last error: {last_exception}")

# ==============================================================================
# STEP 3: VOICE GENERATION (gTTS)
# ==============================================================================
def generate_voiceover(text):
    print("3️⃣ Generating expressive audio track with gTTS...")
    tts = gTTS(text=text, lang='en', tld='com', slow=False)
    tts.save(VOICE_AUDIO)
    
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", VOICE_AUDIO]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 45.0

# ==============================================================================
# STEP 4: ANIMATE IMAGE (Ken Burns Effect via FFmpeg)
# ==============================================================================
def create_zooming_video(duration):
    print("4️⃣ Creating zooming video from static image (Ken Burns effect)...")
    
    # Ensure output doesn't exist
    if os.path.exists(VIDEO_NO_AUDIO):
        os.remove(VIDEO_NO_AUDIO)

    # Calculate target zoom (e.g., zoom from 1.0 to 1.2 over duration)
    # We create a 1080x1920 video (Reels format)
    # The image will be slightly larger than screen, then zoomed in further.
    
    # This complex filter does the following:
    # 1. Sets output size to 1080x1920
    # 2. Scales input image while keeping aspect ratio (crop if necessary to fill)
    # 3. Applies a zoomout effect centered on the image over the calculated duration
    # NOTE: Zooming on CPU is resource intensive.
    
    # Simplified zoom filter for better CPU performance:
    zoom_cmd = (
        f"zoompan=z='min(zoom+0.0015,{duration/20})':d={duration*25}:s=1080x1920:fps=25"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", # Loop the image input
        "-i", GENERATED_IMAGE,
        "-vf", zoom_cmd,
        "-t", str(duration + 1), # Set duration matching audio
        "-pix_fmt", "yuv420p",
        VIDEO_NO_AUDIO
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    print("✅ Zooming video created.")

# ==============================================================================
# STEP 5: MERGE AUDIO + VIDEO AND ADD TEXT OVERLAYS
# ==============================================================================
def render_final_reel(data, audio_duration):
    print("5️⃣ Merging audio and overlaying text tiles...")
    
    switch_time = audio_duration / 2.0 
    target_w, target_h = 1080, 1920

    # Load the zooming video clip
    video_clip = VideoFileClip(VIDEO_NO_AUDIO)
    
    # Add the generated audio to the video
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    audio_clip = AudioFileClip(VOICE_AUDIO)
    final_video = video_clip.with_audio(audio_clip)
    
    # Define Text Area
    text_area_w = target_w - 100
    text_area_h = target_h // 2 # Use top half

    # --------------------------------------------------
    # Question Overlay
    # --------------------------------------------------
    q_text = (
        f"DAILY PMP PREP: {data['topic'].upper()}\n\n"
        f"{data['question']}\n\n"
        f"{data['option_a']}\n{data['option_b']}\n{data['option_c']}\n{data['option_d']}"
    )
    
    # Add a semi-transparent background box for the text using a ColorClip
    q_text_clip = TextClip(
        text=q_text,
        font_size=45,
        color='white',
        font='Arial-Bold',
        method='caption',
        size=(text_area_w, text_area_h)
    ).with_position(('center', 50)).with_start(0).with_duration(switch_time)

    # Optional: Create a semi-transparent black box behind the text for readability
    q_box = ColorClip(size=(text_area_w, text_area_h + 100), color=(0,0,0)).with_opacity(0.6).with_position(('center', 30)).with_start(0).with_duration(switch_time)


    # --------------------------------------------------
    # Answer Overlay
    # --------------------------------------------------
    a_text = (
        f"CORRECT ANSWER:\n{data['correct_answer']}\n\n"
        f"EXPLANATION:\n{data['explanation']}\n\n"
        f"👍 Like & Follow for Daily PMP Prep!"
    )
    
    a_text_clip = TextClip(
        text=a_text,
        font_size=50,
        color='yellow',
        font='Arial-Bold',
        method='caption',
        size=(text_area_w, text_area_h)
    ).with_position(('center', 50)).with_start(switch_time).with_duration(audio_duration - switch_time + 1.0)
    
    a_box = ColorClip(size=(text_area_w, text_area_h + 100), color=(0,0,0)).with_opacity(0.6).with_position(('center', 30)).with_start(switch_time).with_duration(audio_duration - switch_time + 1.0)

    # Compose layers
    final = CompositeVideoClip([final_video, q_box, q_text_clip, a_box, a_text_clip])
    
    print("Writing final video file...")
    try:
        final.write_videofile(
            FINAL_REEL, 
            fps=25, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast" # Crucial for speed on Actions
        )
        print("✅ Final animated Reel exported!")
    finally:
        video_clip.close()
        final_video.close()
        audio_clip.close()
        final.close()

# ==============================================================================
# STEP 6: PUBLISH TO FACEBOOK
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
    # 1. Generate Image (Fallback to red box if SD fails)
    generate_host_image()
    
    # 2. Get Content from Gemini
    content = get_daily_pmp_content()
    
    # 3. Generate Audio (gTTS)
    audio_dur = generate_voiceover(content["spoken_script"])
    
    # 4. Animate Image using FFmpeg zoompan
    create_zooming_video(audio_dur)
    
    # 5. Composite Audio, Video, and Text
    render_final_reel(content, audio_dur)
    
    # 6. Publish
    if FB_PAGE_ID and FB_ACCESS_TOKEN:
        publish_to_facebook()
    else:
        print("Facebook credentials not found. Video rendered locally only.")
