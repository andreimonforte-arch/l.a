from PIL import Image, ImageDraw
import os

from app import app

# Ensure directories exist
os.makedirs(os.path.join(app.static_folder, 'uploads'), exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'images'), exist_ok=True)

# Create placeholder if it doesn't exist
placeholder_path = os.path.join(app.static_folder, 'images', 'placeholder.png')
if not os.path.exists(placeholder_path):
    img = Image.new('RGB', (400, 400), color='#e9ecef')
    draw = ImageDraw.Draw(img)
    text = "No Image"
    draw.text((150, 190), text, fill='#adb5bd')
    img.save(placeholder_path)
    print("✓ Placeholder image created")