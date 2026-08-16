import os
import json
import time
import subprocess
import random
import requests
from google import genai
from gtts import gTTS
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
VOICE_AUDIO = os.path.join(ROOT_DIR, "speech.mp3")
FINAL_REEL = os.path.join(ROOT_DIR, "daily_pmp_reel.mp4")

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
# STEP 2: 20 DIVERSE CHARACTER & SETTING COMBINATIONS (PETEY FEATURED IN A FEW)
# ==============================================================================
character_settings_pool = [
    # 1. Andrew alone (Office)
    "Andrew the golden retriever wearing a tiny project management hard hat and holding a clipboard inside a modern sunlit tech startup open-office",
    # 2. Andrew & Petey together (Treehouse)
    "Andrew the golden retriever puppy collaborating with Petey, a clever white-and-black pit bull mix with a black patch over his left eye, inside a cozy rustic wooden treehouse study room",
    # 3. Solo character 1 (Sci-Fi Command Center)
    "a charismatic 3D animated ginger cat wearing a sleek headset inside a futuristic sci-fi command center with glowing holographic project schedules",
    # 4. Solo character 2 (Beachside Patio)
    "an enthusiastic 3D animated golden retriever puppy wearing tropical sunglasses on a bright beachside patio overlooking the ocean",
    # 5. Andrew & Petey together (Workshop)
    "Andrew the golden retriever reviewing agile boards alongside Petey, an energetic white-and-black pit bull mix with a unique black patch over his left eye, in a vintage tech workshop",
    # 6. Solo character 3 (University Lecture Hall)
    "a smart 3D animated border collie wearing professor glasses in a sunlit university lecture hall with tiered wooden desks",
    # 7. Solo character 4 (Project War Room)
    "a focused 3D animated silver fox wearing a sharp business suit inside a high-tech project management war room featuring digital Gantt charts",
    # 8. Solo character 5 (Silicon Valley Incubator)
    "an energetic 3D animated brown bear wearing a hoodie inside a sleek Silicon Valley incubator space with exposed brick walls",
    # 9. Andrew & Petey together (Modern Conference Room)
    "Andrew the golden retriever and Petey, a white-and-black pit bull mix with a black patch over his left eye, brainstorming around a glass conference table with sticky notes",
    # 10. Solo character 6 (Cozy Library)
    "a wise old 3D animated owl wearing a graduation cap sitting inside a cozy wood-paneled library surrounded by PMBOK guide books",
    # 11. Solo character 7 (Agile Scrum Board Room)
    "an ambitious 3D animated red panda pointing at a colorful Kanban agile board covered in sticky notes",
    # 12. Solo character 8 (Executive Boardroom)
    "a professional 3D animated beagle wearing a navy blue blazer inside a high-rise corporate executive boardroom",
    # 13. Solo character 9 (Data Analytics Lab)
    "a tech-savvy 3D animated squirrel typing furiously on multiple monitors inside a sleek data analytics laboratory",
    # 14. Solo character 10 (Outdoor Campfire Strategy Session)
    "an adventurous 3D animated husky puppy reviewing project milestones next to a warm campfire under a starry night sky",
    # 15. Andrew alone (Modern Studio)
    "Andrew the golden retriever puppy holding a colorful Gantt chart in a minimalist Pixar-style digital design studio with vibrant lighting",
    # 16. Solo character 11 (Construction Site Trailer)
    "a tough 3D animated bulldog wearing a high-visibility safety vest inside a project site management trailer",
    # 17. Solo character 12 (Creative Agency Loft)
    "a trendy 3D animated otter wearing stylish round glasses inside a sunlit creative agency loft with indoor plants",
    # 18. Solo character 13 (Financial District Balcony)
    "a sharp 3D animated rabbit wearing a pinstripe vest standing on a glass balcony overlooking a bustling financial district",
    # 19. Solo character 14 (Innovation Hub)
    "a cheerful 3D animated kangaroo holding architectural blueprints inside a futuristic glass innovation hub",
    # 20. Solo character 15 (Solar-powered Greenhouse Studio)
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
        f"Create a rigorous, situational PMP exam practice question specifically focused on: {selected_topic}, "
        "alongside a lively, highly expressive spoken script for the 3D animated animal host to present in a short-form video. "
        "Use exclamation points, question marks, and natural pauses (using ellipses) in the spoken script so the voice engine sounds dynamic and engaging. "
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
        '    "spoken_script": "Hey team! Are you ready for today\'s PMP challenge? Listen closely... [Question introduction]? Is it Option A... [detail]? Option B... [detail]? Think carefully!"\n'
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
        print(f"--- Starting content generation attempt {attempt}/3 ---")
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
                    raw_text = raw_text.split("```")[1].split("```")[0]
                return json.loads(raw_text.strip())
            except Exception as e:
                last_exception = e
                print(f"⚠️ Model {model_name} failed: {e}")
                if "503" in str(e):
                    print("Server overloaded (503). Pausing briefly before next model...")
                    time.sleep(10)
                continue
        
        wait_time = attempt * 15
        print(f"All models failed on attempt {attempt}. Waiting {wait_time} seconds before retrying...")
        time.sleep(wait_time)
            
    raise Exception(f"All models and retries failed. Last error: {last_exception}")

# ==============================================================================
# STEP 4: GENERATE CHARACTER PORTRAIT NATIVELY VIA GEMINI
# ==============================================================================
def generate_character_image():
    print("2️⃣ Generating Pixar-style character portrait via Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    selected_combo = random.choice(character_settings_pool)
    
    image_prompt = (
        f"A striking vertical portrait shot in the distinct visual style of Pixar and Disney, "
        f"featuring {selected_combo}, "
        "facing the camera directly, talking and expressive, vibrant studio lighting, polished cinematic digital rendering, perfect vertical mobile composition."
    )
    
    image_models_to_try = ["gemini-2.5-flash", "gemini-3.1-flash-image", "gemini-3.1-flash-image-preview"]
    image_bytes = None
    
    for img_model in image_models_to_try:
        try:
            response = client.models.generate_content(
                model=img_model,
                contents=image_prompt,
            )
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.inline_data and part.inline_data.data:
                        image_bytes = part.inline_data.data
                        break
                if image_bytes:
                    break
            if image_bytes:
                print(f"Successfully generated character image using model: {img_model}")
                break
        except Exception as e:
            print(f"Image model {img_model} failed: {e}. Trying next...")
            
    if not image_bytes:
        raise Exception("All Gemini image generation models failed.")
        
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img.save(GENERATED_IMAGE)
    print("Character image successfully saved!")

# ==============================================================================
# STEP 5: EXPRESSIVE VOICE GENERATION (gTTS)
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
# STEP 6: RENDER TALKING REEL (STATIC PORTRAIT + AUDIO + TEXT OVERLAYS)
# ==============================================================================
def render_final_reel(data, audio_duration):
    print("5️⃣ Assembling talking character Reel...")
    
    switch_time = audio_duration / 2.0 
    target_w, target_h = 1080, 1920

    from moviepy.video.VideoClip import TextClip, ColorClip, ImageClip
    from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip

    image_clip = ImageClip(GENERATED_IMAGE).with_duration(audio_duration + 1.0).resize(newsize=(target_w, target_h))
    audio_clip = AudioFileClip(VOICE_AUDIO)
    video_with_audio = image_clip.with_audio(audio_clip)
    
    text_area_w = target_w - 100
    text_area_h = 700

    q_text = (
        f"★ DAILY PMP PREP ★\n\n"
        f"{data['question']}\n\n"
        f"{data['option_a']}\n{data['option_b']}\n{data['option_c']}\n{data['option_d']}"
    )
    
    q_text_clip = TextClip(
        text=q_text,
        font_size=38,
        color='white',
        font='Arial-Bold',
        method='caption',
        size=(text_area_w, text_area_h)
    ).with_position(('center', 100)).with_start(0).with_duration(switch_time)

    q_box = ColorClip(size=(text_area_w, text_area_h + 50), color=(15, 23, 42)).with_opacity(0.85).with_position(('center', 80)).with_start(0).with_duration(switch_time)

    a_text = (
        f"✅ CORRECT ANSWER:\n{data['correct_answer']}\n\n"
        f"🧠 MINDSET:\n{data['explanation']}\n\n"
        f"👍 Like & Follow for Daily PMP Prep!"
    )
    
    a_text_clip = TextClip(
        text=a_text,
        font_size=42,
        color='yellow',
        font='Arial-Bold',
        method='caption',
        size=(text_area_w, text_area_h)
    ).with_position(('center', 100)).with_start(switch_time).with_duration(audio_duration - switch_time + 1.0)
    
    a_box = ColorClip(size=(text_area_w, text_area_h + 50), color=(15, 23, 42)).with_opacity(0.85).with_position(('center', 80)).with_start(switch_time).with_duration(audio_duration - switch_time + 1.0)

    final = CompositeVideoClip([video_with_audio, q_box, q_text_clip, a_box, a_text_clip])
    
    print("Writing final video file...")
    try:
        final.write_videofile(
            FINAL_REEL, 
            fps=25, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast"
        )
        print("✅ Final talking character Reel exported!")
    finally:
        image_clip.close()
        video_with_audio.close()
        audio_clip.close()
        final.close()

# ==============================================================================
# STEP 7: PUBLISH TO FACEBOOK
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
    content = get_daily_pmp_content()
    generate_character_image()
    audio_dur = generate_voiceover(content["spoken_script"])
    render_final_reel(content, audio_dur)
    
    if FB_PAGE_ID and FB_ACCESS_TOKEN:
        publish_to_facebook()
    else:
        print("Facebook credentials not found. Video rendered locally only.")
