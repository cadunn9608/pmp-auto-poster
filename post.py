import os
import requests
import random
from datetime import date
from google import genai
from google.genai import types
from PIL import Image
import io

# Initialize the Gemini client
client = genai.Client()

# --- Configuration for Characters and Layout ---
CHARACTER_ASSETS = [
    "assets/beagle_with_toy.png",
    "assets/scruffy_puppy.png"
]
TEXT_BOX_ASSET = "assets/pmp_textbox.png"
OUTPUT_IMAGE_NAME = "pmp_daily_image.png"

# --- Predefined Background Themes ---
BACKGROUND_THEMES = [
    "a cozy, book-filled home study",
    "a bright, sunny park bench",
    "a minimalist, modern co-working space",
    "a bustling, futuristic tech lab",
    "a serene Japanese garden with cherry blossoms",
]

def generate_pmp_tip():
    """Generates a daily PMP tip using Gemini with fallback model logic."""
    prompt = (
        "Write a concise, professional PMP Tip of the Day focusing on project management "
        "best practices, Agile, or PMI frameworks. Keep it under 60 words."
    )
    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"]
    
    for model_name in models_to_try:
        try:
            print(f"Trying to generate tip with model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                return response.text
        except Exception as e:
            print(f"Model {model_name} failed with error: {e}")
            continue
            
    raise Exception("All model generation attempts failed.")

def generate_dynamic_background(theme):
    """Generates a background image using Gemini based on a theme with 3D Pixar style."""
    print(f"Generating a new background: {theme}...")
    prompt = (
        f"A 3D digital render of {theme}, in the distinct visual style of a "
        "modern Pixar animated film. Volumetric studio lighting, rich depth of "
        "field, smooth surfaces, charming and warm aesthetic, 3D computer animation "
        "frame. The composition should have open space for overlaying characters "
        "and a text box."
    )
    
    # Using generate_content with a multimodal/image generation capable model endpoint
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="image/jpeg"
        )
    )
    
    # Extract image bytes from the response parts
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            return Image.open(io.BytesIO(part.inline_data.data))
            
    raise Exception("Failed to generate background image content.")

def composite_final_image(background_pil):
    """Layers characters and the text box onto the background."""
    print("Compositing final image...")
    canvas = background_pil.copy()

    for asset_path in CHARACTER_ASSETS:
        if os.path.exists(asset_path):
            char_image = Image.open(asset_path).convert("RGBA")
            canvas.paste(char_image, (0, 0), char_image)
        else:
            print(f"Warning: Character asset not found at {asset_path}")

    if os.path.exists(TEXT_BOX_ASSET):
        text_box_image = Image.open(TEXT_BOX_ASSET).convert("RGBA")
        canvas.paste(text_box_image, (0, 0), text_box_image)
    else:
        print(f"Warning: Text box asset not found at {TEXT_BOX_ASSET}")

    canvas.save(OUTPUT_IMAGE_NAME, "PNG")
    print(f"Saved final image to {OUTPUT_IMAGE_NAME}")

def post_to_facebook(image_path, caption):
    """Publishes an image with a caption to a Facebook Page using the Graph API."""
    page_id = os.environ.get("FACEBOOK_PAGE_ID")
    access_token = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
    url = f"https://graph.facebook.com/v18.0/{page_id}/photos"

    with open(image_path, "rb") as image_file:
        files = {"source": image_file}
        payload = {"message": caption, "access_token": access_token}
        response = requests.post(url, data=payload, files=files)
        result = response.json()

        if "id" in result:
            print(f"Successfully posted to Facebook! Post ID: {result['id']}")
        else:
            print(f"Failed to post: {result}")

if __name__ == "__main__":
    tip_text = generate_pmp_tip()
    print(f"Generated Tip:\n{tip_text}")

    caption = f"PMP Tip of the Day - {date.today()}:\n\n{tip_text}"
    selected_theme = random.choice(BACKGROUND_THEMES)
    background_image = generate_dynamic_background(selected_theme)
    composite_final_image(background_image)
    # post_to_facebook(OUTPUT_IMAGE_NAME, caption)
