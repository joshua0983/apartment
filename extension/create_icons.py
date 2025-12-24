"""
Simple script to create placeholder icons for the extension.
Run: python extension/create_icons.py
"""

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'Pillow'])
    from PIL import Image, ImageDraw, ImageFont

import os

def create_icon(size, filename):
    # Create a gradient background
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple building emoji-style icon
    # Building body
    building_width = int(size * 0.6)
    building_height = int(size * 0.7)
    x1 = (size - building_width) // 2
    y1 = size - building_height - int(size * 0.1)
    x2 = x1 + building_width
    y2 = size - int(size * 0.1)
    
    draw.rectangle([x1, y1, x2, y2], fill='#ffffff', outline='#333333', width=max(1, size // 64))
    
    # Windows
    window_size = int(size * 0.08)
    window_gap = int(size * 0.05)
    
    for row in range(4):
        for col in range(3):
            wx = x1 + window_gap + col * (window_size + window_gap)
            wy = y1 + window_gap + row * (window_size + window_gap)
            if wy + window_size < y2:
                draw.rectangle([wx, wy, wx + window_size, wy + window_size], 
                             fill='#667eea', outline='#333333', width=max(1, size // 128))
    
    # Save
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(script_dir, 'icons')
    os.makedirs(icons_dir, exist_ok=True)
    filepath = os.path.join(icons_dir, filename)
    img.save(filepath)
    print(f'Created {filepath}')

if __name__ == '__main__':
    # Create all three sizes
    create_icon(16, 'icon16.png')
    create_icon(48, 'icon48.png')
    create_icon(128, 'icon128.png')
    
    print('✅ All icons created successfully!')
