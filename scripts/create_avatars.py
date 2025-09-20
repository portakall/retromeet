import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def create_avatar(filename, color, text):
    """Create a simple avatar image with a colored background and text"""
    # Create a 200x200 image with the specified background color
    img = Image.new('RGB', (200, 200), color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a system font, or fall back to default
    try:
        font = ImageFont.truetype("Arial", 60)
    except IOError:
        font = ImageFont.load_default()
    
    # Calculate text position to center it
    text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:4]
    position = ((200 - text_width) // 2, (200 - text_height) // 2)
    
    # Draw the text in white
    draw.text(position, text, fill="white", font=font)
    
    # Save the image
    img.save(filename)
    print(f"Created avatar: {filename}")

def main():
    """Create sample avatar images"""
    avatar_dir = "frontend/static/avatars"
    os.makedirs(avatar_dir, exist_ok=True)
    
    # Remove existing placeholder files
    for file in os.listdir(avatar_dir):
        if file.endswith(".png"):
            os.remove(os.path.join(avatar_dir, file))
    
    # Create new avatar images
    avatars = [
        ("avatar1.png", "blue", "JD"),
        ("avatar2.png", "green", "JS"),
        ("avatar3.png", "purple", "BJ"),
        ("avatar4.png", "red", "AB"),
        ("avatar5.png", "orange", "CD")
    ]
    
    for filename, color, text in avatars:
        create_avatar(os.path.join(avatar_dir, filename), color, text)

if __name__ == "__main__":
    main()
