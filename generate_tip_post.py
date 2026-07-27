# 3. Overlay with Corrected Width and Safer Wrapping to Prevent Overflow
print("Overlaying PMP tip on image...")
img = Image.open(image_bytes).convert("RGB")
width, height = img.size

font_size = max(20, int(height * 0.030))
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
except IOError:
    font = ImageFont.load_default()

draw = ImageDraw.Draw(img)

# Balanced margins so the box has a clean border on both left and right
margin = int(width * 0.06)
text_box_w = width - (2 * margin)

# Tighter character limit to guarantee text stays safely inside the right border
char_limit = int(text_box_w / (font_size * 0.52))
wrapped_lines = textwrap.wrap(ai_tip_raw, width=char_limit)

line_height = font_size + 10
text_box_h = (len(wrapped_lines) * line_height) + 36

# Positioned near the bottom edge
text_box_y = height - text_box_h - int(height * 0.04)
text_box_x = margin

overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)
overlay_draw.rounded_rectangle(
    [text_box_x, text_box_y, text_box_x + text_box_w, text_box_y + text_box_h],
    radius=18,
    fill=(15, 23, 42, 245),
    outline=(255, 255, 255, 180),
    width=3
)
img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
draw = ImageDraw.Draw(img)

current_y = text_box_y + 18
for line in wrapped_lines:
    draw.text((text_box_x + 18, current_y), line, fill="white", font=font)
    current_y += line_height

img.save(image_path)
print("Text box margins and wrapping successfully corrected!")
