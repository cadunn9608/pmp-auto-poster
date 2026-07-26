import os
import time
import requests
from google import genai
from moviepy import ImageClip, TextClip, CompositeVideoClip, ColorClip

# Initialize Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def generate_reel_content():
    """Uses Gemini to generate the PMP question, answers, and caption."""
    prompt = """
    You are creating a daily PMP practice question for a Facebook Reel featuring Andrew (teacher) and Petey (student). 
    Provide the output in the following clean format:
    QUESTION: [A short, punchy PMP question]
    OPTION_A: [Choice A]
    OPTION_B: [Choice B]
    OPTION_C: [Choice C]
    OPTION_D: [Choice D]
    CORRECT_ANSWER: [Letter and text]
    EXPLANATION: [A brief 2-sentence explanation from Andrew]
    CAPTION: [An engaging Facebook caption with hashtags for the Reel]
    """
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )
    return response.text

def create_vertical_reel(character_image_path, output_filename="daily_pmp_reel.mp4"):
    # Create vertical 9:16 background (1080x1920)
    bg_clip = ColorClip(size=(1080, 1920), color=(30, 40, 30), duration=15.0)
    
    # Place Andrew & Petey character image
    character_clip = ImageClip(character_image_path).with_duration(15.0)
    character_clip = character_clip.resized(width=800).with_position(("center", 1000))
    
    # Blackboard text layout
    blackboard_text = (
        "PMP QUESTION OF THE DAY\n\n"
        "Which of the following is a key output\n"
        "of the Define Scope process?\n\n"
        "A) Project Charter\n"
        "B) Scope Baseline\n"
        "C) Project Scope Statement\nD) WBS"
    )
    
    txt_clip = TextClip(
        text=blackboard_text, 
        font_size=40, 
        color='white', 
        size=(950, 800),
        method='caption',
        horizontal_align='center',
        vertical_align='center'
    ).with_duration(15.0).with_position(("center", 120))
    
    # Composite and write video
    video = CompositeVideoClip([bg_clip, txt_clip, character_clip])
    video.write_videofile(output_filename, fps=24, codec='libx264', audio_codec='aac')
    print(f"Reel successfully created: {output_filename}")

def post_reel_to_facebook(video_path, caption_text):
    """Automatically publishes an official Facebook Reel using Meta's Container API."""
    page_id = os.environ.get("FB_PAGE_ID")
    access_token = os.environ.get("FB_ACCESS_TOKEN")
    
    if not page_id or not access_token:
        print("Facebook credentials missing. Skipping auto-post.")
        return

    print("Initializing Facebook Reel container...")
    url = f"https://graph.facebook.com/v19.0/{page_id}/video_reels"
    
    # Step 1: Initialize the Reel container
    init_payload = {
        "upload_phase": "start",
        "access_token": access_token
    }
    init_response = requests.post(url, data=init_payload).json()
    
    if "video_id" not in init_response:
        print("Failed to initialize Reel container:", init_response)
        return
        
    video_id = init_response["video_id"]
    upload_url = init_response["upload_url"]
    
    print(f"Container created (ID: {video_id}). Uploading video binary...")
    
    # Step 2: Upload the video file bytes to the upload URL
    with open(video_path, "rb") as video_file:
        headers = {
            "Authorization": f"OAuth {access_token}",
            "file_url": upload_url
        }
        files = {"source": video_file}
        upload_response = requests.post(upload_url, headers=headers, files=files)
        
    if upload_response.status_code != 200:
        print("Failed to upload video binary:", upload_response.text)
        return

    print("Video binary uploaded. Waiting 15 seconds for Meta processing...")
    time.sleep(15)

    # Step 3: Publish the processed Reel container
    publish_payload = {
        "upload_phase": "finish",
        "video_id": video_id,
        "video_state": "PUBLISHED",
        "description": caption_text,
        "access_token": access_token
    }
    publish_response = requests.post(url, data=publish_payload).json()
    print("Facebook Reel Publish Response:", publish_response)

if __name__ == "__main__":
    print("Generating Andrew & Petey PMP content...")
    content = generate_reel_content()
    print("Generated Content:\n", content)
    
    create_vertical_reel("Gemini_Generated_Image_eh74r1eh74r1eh74.png")
    
    caption = "PMP Question of the Day with Andrew & Petey! Test your project management skills. #PMP #ProjectManagement #PMPExam"
    post_reel_to_facebook("daily_pmp_reel.mp4", caption)
