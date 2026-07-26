import os
from google import genai
from moviepy import ImageClip, TextClip, CompositeVideoClip, ColorClip

# Initialize the Gemini client using the environment variable
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def generate_reel_content():
    """Uses Gemini to generate the PMP question, answers, and the Andrew & Petey interaction script."""
    prompt = """
    You are creating a daily PMP practice question for a Facebook Reel featuring two animated characters: 
    - Andrew (a Golden Retriever who acts as the smart, patient teacher)
    - Petey (a spotted terrier mix who acts as the eager student)

    Provide the output in the following clean format:
    QUESTION: [A short, punchy PMP question]
    OPTION_A: [Choice A]
    OPTION_B: [Choice B]
    OPTION_C: [Choice C]
    OPTION_D: [Choice D]
    CORRECT_ANSWER: [Letter and text]
    EXPLANATION: [A brief, 2-sentence explanation from Andrew teaching Petey]
    PETEY_ACTION: [A short note on Petey's cute reaction, e.g., "Petey nods understandingly with a smile"]
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text

def create_vertical_reel(character_image_path, output_filename="daily_pmp_reel.mp4"):
    # 1. Create a vertical 9:16 background (1080x1920) for the classroom / blackboard
    bg_clip = ColorClip(size=(1080, 1920), color=(30, 40, 30), duration=15.0)
    
    # 2. Load and place the Andrew & Petey character image
    character_clip = ImageClip(character_image_path).with_duration(15.0)
    character_clip = character_clip.resized(width=800).with_position(("center", 1000))
    
    # 3. Blackboard text layout for Question & Multiple Choice Options
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
    
    # 4. Composite and write video
    video = CompositeVideoClip([bg_clip, txt_clip, character_clip])
    video.write_videofile(output_filename, fps=24, codec='libx264', audio_codec='aac')
    print(f"Andrew & Petey Reel successfully created: {output_filename}")

if __name__ == "__main__":
    print("Generating Andrew & Petey PMP content...")
    content = generate_reel_content()
    print("Generated Content:\n", content)
    
    # Point to your uploaded character image in the root folder
    create_vertical_reel("Gemini_Generated_Image_eh74r1eh74r1eh74.png")
