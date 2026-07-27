# 3. Overlay the PMP Tip Text cleanly on the Generated Image using Pillow
print("Overlaying PMP tip on image...")
img = Image.open(image_bytes).convert("RGB")
width, height = img.size

# Increased font size for better readability (using ~3.2% of total image height)
font_size = max(18, int(height * 0.032))
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
except IOError:
    font = ImageFont.load_default()

draw = ImageDraw.Draw(img)

# Wider margin and larger text container box
margin = int(width * 0.04)
text_box_w = width - (2 * margin)

# Adjust character limit for the larger font size
char_limit = int(text_box_w / (font_size * 0.50))
wrapped_lines = textwrap.wrap(ai_tip_raw, width=char_limit)

# Taller box height to comfortably fit larger multi-line text with spacious padding
line_height = font_size + 10
text_box_h = (len(wrapped_lines) * line_height) + 40
text_box_y = height - text_box_h - int(height * 0.05)
text_box_x = margin

# Draw a larger semi-transparent dark background box for high contrast and readability
overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)
overlay_draw.rounded_rectangle(
    [text_box_x, text_box_y, text_box_x + text_box_w, text_box_y + text_box_h],
    radius=16,
    fill=(15, 23, 42, 235), # Deep rich dark slate background
    outline=(255, 255, 255, 140), # Brighter crisp border outline
    width=3
)
img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
draw = ImageDraw.Draw(img)

# Draw wrapped text lines line by line with clear vertical padding
current_y = text_box_y + 20
for line in wrapped_lines:
    draw.text((text_box_x + 20, current_y), line, fill="white", font=font)
    current_y += line_height

img.save(image_path)
print("Larger branded text box successfully applied!")
