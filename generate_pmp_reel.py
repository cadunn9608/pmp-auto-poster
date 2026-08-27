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
from google.genai import types
from PIL import Image
from io import BytesIO

import builtins
def print(*args, **kwargs):
    kwargs['flush'] = True
    builtins.print(*args, **kwargs)

print("🚀 SCRIPT INITIATED: Full-Length Natural Audio & Precision Lip-Sync Pipeline...")

# ==============================================================================
# CONFIGURATION & ABSOLUTE PATH SETUP
# ==============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID") or os.environ.get("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FACEBOOK_ACCESS_TOKEN") or os.environ.get("FB_ACCESS_TOKEN")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

GENERATED_IMAGE = os.path.join(ROOT_DIR, "host_character.png")
VOICE_AUDIO_MP3 = os.path.join(ROOT_DIR, "speech_original.mp3")
VIDEO_LIPSYNC = os.path.join(ROOT_DIR, "talking_head.mp4")
FINAL_REEL = os.path.join(ROOT_DIR, "daily_pmp_reel.mp4")

def validate_environment():
    missing = []
    if not GEMINI_API_KEY or not GEMINI_API_KEY.strip(): missing.append("GEMINI_API_KEY")
    if not FB_PAGE_ID or not FB_PAGE_ID.strip(): missing.append("FACEBOOK_PAGE_ID")
    if not FB_ACCESS_TOKEN or not FB_ACCESS_TOKEN.strip(): missing.append("FACEBOOK_ACCESS_TOKEN")
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
    "A clean, symmetrical, front-facing 3D Pixar style portrait of a golden retriever wearing a tiny project management hard hat. Looking straight ahead at the camera, clear jawline, distinct mouth, studio lighting.",
    "A clean, symmetrical, front-facing 3D Pixar style portrait of a friendly ginger cat wearing a sleek headset. Looking straight ahead at the camera, clear visible mouth, studio lighting.",
    "A clean, symmetrical, front-facing 3D Pixar style portrait of a golden retriever puppy wearing sunglasses. Looking straight ahead at the camera, clear visible mouth, vibrant lighting."
]

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
    
    # Updated Gemini 3.x series models
    candidate_models = [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.1-flash",
        "gemini-3.1-flash-lite",
        "gemini-3-flash-preview"
    ]
    
    # 1. Attempt static list of candidate models
    for model_name in candidate_models:
        try:
            print(f"🔄 Attempting text generation with model '{model_name}'...")
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt, 
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            raw_text = response.text.strip()
            bt = chr(96) * 3
            if f"{bt}json" in raw_text: raw_text = raw_text.split(f"{bt}json")[1].split(bt)[0]
            elif bt in raw_text: raw_text = raw_text.split(bt)[1].split(bt)[0]
            
            parsed = json.loads(raw_text.strip())
            print(f"✅ Text generation succeeded using model '{model_name}'.")
            return parsed
        except Exception as e:
            print(f"⚠️ Generation attempt with model '{model_name}' failed: {e}")

    # 2. Dynamic Fallback: Query available API models if candidates fail
    print("🌐 Hardcoded model attempts failed. Querying active models dynamically from Gemini API...")
    try:
        available_models = list(client.models.list())
        for model in available_models:
            model_id = getattr(model, "name", str(model))
            if "gemini" in model_id.lower() and "tts" not in model_id.lower():
                clean_name = model_id.replace("models/", "")
                try:
                    print(f"🔄 Dynamic fallback attempt with '{clean_name}'...")
                    response = client.models.generate_content(
                        model=clean_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                    raw_text = response.text.strip()
                    bt = chr(96) * 3
                    if f"{bt}json" in raw_text: raw_text = raw_text.split(f"{bt}json")[1].split(bt)[0]
                    elif bt in raw_text: raw_text = raw_text.split(bt)[1].split(bt)[0]
                    
                    parsed = json.loads(raw_text.strip())
                    print(f"✅ Dynamic fallback succeeded with model '{clean_name}'.")
                    return parsed
                except Exception as inner_e:
                    print(f"⚠️ Dynamic attempt with '{clean_name}' failed: {inner_e}")
    except Exception as list_err:
        print(f"⚠️ Failed to list active API models: {list_err}")

    raise RuntimeError("Failed to generate content from Gemini across all fallback mechanisms.")

def generate_character_image():
    print("2️⃣ Generating precision-framed character portrait via Gemini/Imagen...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    selected_prompt = random.choice(character_settings_pool)
    
    # 1. Primary path: Imagen models via generate_images
    imagen_models = ["imagen-3.0-generate-002", "imagen-3.0-fast-generate-001"]
    for img_model in imagen_models:
        try:
            print(f"🔄 Attempting image generation with Imagen model '{img_model}'...")
            response = client.models.generate_images(
                model=img_model,
                prompt=selected_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="9:16"
                )
            )
            if hasattr(response, "generated_images") and response.generated_images:
                gen_img = response.generated_images[0]
                img_bytes = gen_img.image.image_bytes
                img = Image.open(BytesIO(img_bytes)).convert("RGB")
                img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
                img.save(GENERATED_IMAGE)
                print(f"✅ Character image successfully saved using Imagen model '{img_model}'!")
                return
        except Exception as e:
            print(f"⚠️ Imagen generation with model '{img_model}' failed: {e}")

    # 2. Secondary path: Gemini multimodal models via generate_content
    gemini_img_models = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash"]
    for img_model in gemini_img_models:
        try:
            print(f"🔄 Attempting image generation with Gemini model '{img_model}'...")
            response = client.models.generate_content(model=img_model, contents=selected_prompt)
            if hasattr(response, "candidates") and response.candidates:
                for candidate in response.candidates:
                    if not candidate.content: continue
                    for part in candidate.content.parts:
                        if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                            img = Image.open(BytesIO(part.inline_data.data)).convert("RGB")
                            img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
                            img.save(GENERATED_IMAGE)
                            print(f"✅ Character image successfully saved using Gemini model '{img_model}'!")
                            return
        except Exception as e:
            print(f"⚠️ Image generation with Gemini model '{img_model}' failed: {e}")

    raise RuntimeError("Gemini/Imagen image generation failed across all candidate models.")

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

def animate_character_mouth():
    print("4️⃣ Running Wav2Lip with strict mouth-bounding box padding...")
    wav2lip_dir = os.path.join(ROOT_DIR, "Wav2Lip")
    os.makedirs(os.path.join(wav2lip_dir, "temp"), exist_ok=True)
    
    checkpoint = os.path.join(wav2lip_dir, "checkpoints", "wav2lip_gan.pth")
    wav_path = os.path.join(ROOT_DIR, "speech.wav")
    subprocess.run(["ffmpeg", "-y", "-i", VOICE_AUDIO_MP3, wav_path], check=True, capture_output=True)
    
    cmd = [
        "python", "inference.py", 
        "--checkpoint_path", checkpoint,
        "--face", GENERATED_IMAGE,
        "--audio", wav_path, 
        "--outfile", VIDEO_LIPSYNC,
        "--pads", "0", "15", "0", "0",
        "--nosmooth" 
    ]
    
    res = subprocess.run(cmd, cwd=wav2lip_dir, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Wav2Lip Error Output:\n{res.stderr}")
        raise RuntimeError(f"Wav2Lip failed: {res.stderr}")
    print("✅ Wav2Lip precision mouth sync complete!")

def render_clean_reel():
    print("5️⃣ Exporting full-length Reel...")
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip

    video_clip = VideoFileClip(VIDEO_LIPSYNC)
    audio_clip = AudioFileClip(VOICE_AUDIO_MP3)
    final = video_clip.with_audio(audio_clip)
    
    final.write_videofile(
        FINAL_REEL, 
        fps=25, 
        codec="libx264", 
        audio_codec="aac",
        preset="ultrafast",
        logger=None
    )
    
    video_clip.close()
    audio_clip.close()
    final.close()
    print("✅ Full-length Reel exported successfully!")

def publish_to_facebook(content):
    print("6️⃣ Uploading Reel to Facebook Page...")
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

if __name__ == "__main__":
    try:
        validate_environment()
        content = get_daily_pmp_content()
        generate_character_image()
        
        asyncio.run(generate_expressive_voice(content["spoken_script"]))
        animate_character_mouth()
        render_clean_reel()
        publish_to_facebook(content)
        
        print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        print("\n" + "="*60)
        print("🔥 FATAL ERROR CAUGHT IN PIPELINE 🔥")
        print("="*60)
        traceback.print_exc()
        print("="*60)
        sys.exit(1)
