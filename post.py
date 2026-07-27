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

# --- Configuration for Output ---
OUTPUT_IMAGE_NAME = "pmp_daily_image.png"

# --- Predefined Themes for Fully Generated Daily Images ---
IMAGE_THEMES = [
    "A 3D digital render in Pixar animation style of two cute animated puppy characters playing together in a cozy, book-filled home study, featuring a prominent blank white signboard or text box area for text overlay, warm volumetric studio lighting, rich depth of field, charming aesthetic.",
    "A 3D digital render in Pixar animation style of two playful puppy characters playing with a rope toy on a bright sunny park bench, featuring a prominent blank white signboard or text box area for text overlay, warm volumetric studio lighting, rich depth of field, charming aesthetic.",
    "A 3D digital render in Pixar animation style of two cute puppy characters in a minimalist modern co-working space, featuring a prominent blank white signboard or text box area for text overlay, warm volumetric studio lighting, rich depth of field, charming aesthetic.",
    "A 3D digital render in Pixar animation style of two adorable puppy characters inside a bustling futuristic tech lab, featuring a prominent blank white signboard or text box area for text overlay, warm volumetric studio lighting, rich depth of field, charming aesthetic.",
    "A 3D digital render in Pixar animation style of two sweet puppy characters in a serene Japanese garden with cherry blossoms, featuring a prominent blank white signboard or text box area for text overlay, warm volumetric studio lighting, rich depth of field, charming aesthetic."
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

def generate_full_daily_image(theme_prompt):
    """Uses Gemini to generate the complete unique daily image with characters and background."""
    print(f"Generating a brand new unique daily image...")
    
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=theme_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        )
    )
    
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            image = Image.open(io.BytesIO(part.inline_data.data))
            image.save(OUTPUT_IMAGE_NAME, "PNG")
            print(f"Saved generated image to {OUTPUT_IMAGE_NAME}")
            return
            
    raise Exception("Failed to generate the daily image content.")

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
    
    # Pick a random scene theme daily so it's never the same background/setup
    selected_theme_prompt = random.choice(IMAGE_THEMES)
    generate_full_daily_image(selected_theme_prompt)
    
    # post_to_facebook(OUTPUT_IMAGE_NAME, caption)
