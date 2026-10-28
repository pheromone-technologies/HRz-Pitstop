import json
import os
import requests
import io
from PIL import Image

sys_catalog_path = "data/products.json"
test_catalog_path = "test design site/data/products.json"
watermark_path = "images/HRZ_BIKE_LOGO_page-0001-removebg-preview (3)_20250705_182254_0000.png"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def load_watermark():
    if os.path.exists(watermark_path):
        return Image.open(watermark_path).convert('RGBA')
    # Fallback to tools for hrz watermark
    alt_wm = r"e:\coad\tools for hrz\image logo editor\HRZ_BIKE_LOGO_page-0001-removebg-preview (3)_20250705_182254_0000.png"
    if os.path.exists(alt_wm):
        return Image.open(alt_wm).convert('RGBA')
    return None

WATERMARK = load_watermark()

def standardize_and_save(img_source, output_rel_path, target_size=(1000, 1000)):
    """
    Takes a PIL Image, local file path, or URL.
    Places the image onto a pure white canvas (1000x1000) preserving aspect ratio.
    Stamps the HRZ logo in the bottom right corner with safe margins.
    Saves as WebP.
    """
    if isinstance(img_source, str):
        if img_source.startswith('http://') or img_source.startswith('https://'):
            r = requests.get(img_source, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                print(f"Failed to download {img_source}: status {r.status_code}")
                return False
            im = Image.open(io.BytesIO(r.content))
        else:
            if not os.path.exists(img_source):
                print(f"Local file not found: {img_source}")
                return False
            im = Image.open(img_source)
    elif isinstance(img_source, Image.Image):
        im = img_source
    else:
        return False

    im = im.convert('RGBA')

    # Calculate scale to fit within canvas with 80px safe padding
    max_w = target_size[0] - 160
    max_h = target_size[1] - 160
    scale = min(max_w / im.width, max_h / im.height)
    new_w = int(im.width * scale)
    new_h = int(im.height * scale)

    resized_im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Create 1000x1000 pure white canvas
    canvas = Image.new('RGBA', target_size, (255, 255, 255, 255))
    paste_x = (target_size[0] - new_w) // 2
    paste_y = (target_size[1] - new_h) // 2
    canvas.paste(resized_im, (paste_x, paste_y), resized_im)

    # Stamp HRZ watermark
    if WATERMARK:
        wm_scale = 85.0 / WATERMARK.height
        wm_w = int(WATERMARK.width * wm_scale)
        wm_h = int(WATERMARK.height * wm_scale)
        wm_resized = WATERMARK.resize((wm_w, wm_h), Image.Resampling.LANCZOS)
        wm_x = target_size[0] - wm_w - 40
        wm_y = target_size[1] - wm_h - 40
        canvas.paste(wm_resized, (wm_x, wm_y), wm_resized)

    # Convert to RGB and save
    final_rgb = canvas.convert('RGB')
    
    # Save to main repo
    full_out = os.path.normpath(output_rel_path)
    os.makedirs(os.path.dirname(full_out), exist_ok=True)
    final_rgb.save(full_out, 'WEBP', quality=90)

    # Also save to test design site repo
    test_out = os.path.normpath(os.path.join('test design site', output_rel_path))
    os.makedirs(os.path.dirname(test_out), exist_ok=True)
    final_rgb.save(test_out, 'WEBP', quality=90)

    return True

print("Helper standardization engine initialized.")
