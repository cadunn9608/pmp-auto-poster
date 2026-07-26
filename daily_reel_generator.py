import os
import time
import requests
from google import genai
from moviepy import ImageClip, TextClip, CompositeVideoClip, ColorClip

# Initialize Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def get_long_lived_token():
    """Automatically exchanges and refreshes the Facebook token to prevent expiration."""
    app_id = os.environ.get("FB_APP_ID")
    app_secret = os.environ.get("FB_APP_SECRET")
    current_token = os.environ.get("FB_ACCESS_TOKEN")
    
    if not app_id or not app_secret or not current_token:
        print("[DEBUG] App ID or App Secret not provided. Using standard token as-is.")
        return current_token

    print("[DEBUG] Requesting automatic 60-day token refresh from Meta...")
    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": current_token
    }
    
    try:
        response = requests.get(url, params=params).json()
        if "access_token" in response:
            print("[DEBUG SUCCESS] Facebook access token was updated and extended successfully!")
            return response["access_token"]
        else:
            print(f"[DEBUG NOTICE] Token exchange response did not return a new token: {response}")
            return current_token
    except Exception as e:
        print(f"[DEBUG ERROR] Exception during token refresh: {str(e)}")
        return current_token

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
    """Automatically publishes an official Facebook Reel with proper binary upload authorization."""
    page_id = os.environ.get("FB_PAGE_ID")
    access_token = get_long_lived_token()
    
    if not page_id or not access_token:
        print("[DEBUG ERROR] Facebook credentials are missing. Page ID or Access Token not found.")
        return

    url = f"https://graph.facebook.com/v19.0/{page_id}/video_reels"
    
    try:
        # Step 1: Initialize the Reel container
        print(f"[DEBUG] Initializing Facebook Reel container for Page ID: {page_id}...")
        init_payload = {
            "upload_phase": "start",
            "access_token": access_token
        }
        init_response = requests.post(url, data=init_payload)
        print(f"[DEBUG] Init HTTP Status Code: {init_response.status_code}")
        print(f"[DEBUG] Init Raw Response: {init_response.text}")
        
        init_data = init_response.json()
        if "video_id" not in init_data:
            print("[DEBUG ERROR] 'video_id' missing from Meta init response.")
            return
            
        video_id = init_data["video_id"]
        upload_url = init_data["upload_url"]
        
        # Step 2: Stream the local video file binary to Meta's upload URL with explicit Auth header
        print(f"[DEBUG] Container created successfully (ID: {video_id}). Streaming local video binary with authorization...")
        
        if not os.path.exists(video_path):
            print(f"[DEBUG ERROR] Video file not found at path: {video_path}")
            return

        headers = {
            "Authorization": f"OAuth {access_token}"
        }
        
        with open(video_path, "rb") as video_file:
            files = {"source": (video_path, video_file, "video/mp4")}
            upload_response = requests.post(upload_url, headers=headers, files=files)
            
        print(f"[DEBUG] Binary Upload HTTP Status Code: {upload_response.status_code}")
        print(f"[DEBUG] Binary Upload Response Text: {upload_response.text}")
        
        if upload_response.status_code != 200:
            print("[DEBUG ERROR] Binary upload failed to return 200 OK.")
            return

        print("[DEBUG] Video binary uploaded successfully. Waiting 20 seconds for Meta processing...")
        time.sleep(20)

        # Step 3: Publish the container
        print("[DEBUG] Publishing Reel container...")
        publish_payload = {
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": caption_text,
            "access_token": access_token
        }
        publish_response = requests.post(url, data=publish_payload)
        print(f"[DEBUG] Publish HTTP Status Code: {publish_response.status_code}")
        print(f"[DEBUG] Publish Raw Response: {publish_response.text}")

    except Exception as e:
        print(f"[DEBUG EXCEPTION] Exception occurred during Facebook upload: {str(e)}")

if __name__ == "__main__":
    print("Generating Andrew & Petey PMP content...")
    content = generate_reel_content()
    print("Generated Content:\n", content)
    
    create_vertical_reel("Gemini_Generated_Image_eh74r1eh74r1eh74.png")
    
    caption = "PMP Question of the Day with Andrew & Petey! Test your project management skills. #PMP #ProjectManagement #PMPExam"
    post_reel_to_facebook("daily_pmp_reel.mp4", caption)
