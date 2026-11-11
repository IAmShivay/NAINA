# save as create_icons.py and run: python create_icons.py
from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs('naina/web/static/icons', exist_ok=True)

for size in [192, 512]:
    img = Image.new('RGB', (size, size), '#000814')
    draw = ImageDraw.Draw(img)

    # Draw glowing border
    border = size // 20
    draw.rectangle([border, border, size-border, size-border], outline='#00d4ff', width=border//2)

    # Inner decorative ring
    cx, cy, r = size//2, size//2, size//3
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline='#00d4ff', width=border//3)

    # N letter (simple geometric)
    m = size // 4
    lw = max(2, size // 30)
    draw.line([(m, m), (m, size-m)], fill='#00d4ff', width=lw)           # left vertical
    draw.line([(m, m), (size-m, size-m)], fill='#00d4ff', width=lw)      # diagonal
    draw.line([(size-m, m), (size-m, size-m)], fill='#00d4ff', width=lw) # right vertical

    img.save(f'naina/web/static/icons/icon-{size}.png')
    print(f"Created icon-{size}.png")
