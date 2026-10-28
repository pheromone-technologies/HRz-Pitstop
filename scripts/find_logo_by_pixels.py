import os
from PIL import Image

# Search for the Auto Warrior logo image
# In screenshot 4, the image is predominantly white with red/black text.
# Let's check images in images_processed/
print("Scanning image files...")
logo_candidates = []

for root, dirs, files in os.walk('images_processed'):
    for f in files:
        if f.endswith('.webp'):
            full = os.path.join(root, f)
            try:
                im = Image.open(full)
                # Auto Warrior image in screenshot 4 is a white background image (high R, G, B near 255)
                # and contains the text Auto Warrior with a red car/gauge.
                # Let's check if the image has mostly white pixels
                if im.mode in ('RGB', 'RGBA'):
                    # Sample some pixels
                    im_rgb = im.convert('RGB')
                    w, h = im_rgb.size
                    # Check corners and center
                    tl = im_rgb.getpixel((10, 10))
                    tr = im_rgb.getpixel((w - 10, 10))
                    center = im_rgb.getpixel((w // 2, h // 2))
                    # If top corners are white:
                    if tl[0] > 240 and tl[1] > 240 and tl[2] > 240 and tr[0] > 240 and tr[1] > 240 and tr[2] > 240:
                        # Check if center is dark or red (Auto Warrior logo text)
                        # The word Warrior is dark red: R around 150-200, G < 50, B < 50
                        # Let's sample a small grid
                        has_red = False
                        has_black = False
                        pixels = list(im_rgb.resize((50, 50)).getdata())
                        red_pixels = sum(1 for p in pixels if p[0] > 120 and p[1] < 60 and p[2] < 60)
                        black_pixels = sum(1 for p in pixels if p[0] < 80 and p[1] < 80 and p[2] < 80)
                        white_pixels = sum(1 for p in pixels if p[0] > 230 and p[1] > 230 and p[2] > 230)
                        
                        # In the Auto Warrior logo: white background (>60%), some red (~5-15%), some dark (~5-15%)
                        if white_pixels > 1500 and red_pixels > 20 and black_pixels > 50:
                            logo_candidates.append((full, white_pixels, red_pixels, black_pixels))
            except Exception as e:
                pass

print(f"Found {len(logo_candidates)} potential logo matches:")
for c in logo_candidates:
    print(f"  {c[0]} | white={c[1]}, red={c[2]}, black={c[3]}")
