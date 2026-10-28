import os
import sys
import json
from PIL import Image
import numpy as np
from concurrent.futures import ThreadPoolExecutor

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print(f"Total storefront products: {len(products)}", flush=True)

LOGO_KEYWORDS = [
    'logo', 'banner', 'youtube', 'autowarrior', 'autonity', 'a.webp',
    'social_share', 'motodrift', 'bkwgears', 'page_logo', 'icon'
]

def check_product(p):
    pname = p.get('name', '')
    img_rel = p.get('image', '')
    if not img_rel:
        return None
        
    img_lower = img_rel.lower()
    if any(k in img_lower for k in LOGO_KEYWORDS):
        return ('logo', pname, img_rel, 'keyword_in_filename')

    full_path = os.path.join(r"E:\coad\hrx website 2", img_rel.replace('/', os.sep))
    if not os.path.exists(full_path):
        return ('missing', pname, img_rel, 'file_not_found')

    try:
        with Image.open(full_path) as im:
            if im.mode == 'RGBA':
                # Sample 4 corners alpha
                w, h = im.size
                alpha_corners = [
                    im.getpixel((0, 0))[3],
                    im.getpixel((w - 1, 0))[3],
                    im.getpixel((0, h - 1))[3],
                    im.getpixel((w - 1, h - 1))[3]
                ]
                if sum(alpha_corners) == 0:
                    # Clean transparent corners
                    return None
            
            # Check edge brightness
            small = im.convert('RGB').resize((16, 16))
            arr = np.array(small)
            edge_mean = (arr[0, :].mean() + arr[-1, :].mean() + arr[:, 0].mean() + arr[:, -1].mean()) / 4.0
            if edge_mean < 25:
                return ('black_bg', pname, img_rel, edge_mean)
    except Exception as e:
        return None
    return None

with ThreadPoolExecutor(max_workers=16) as pool:
    results = list(pool.map(check_product, products))

black_bg_prods = [r for r in results if r and r[0] == 'black_bg']
logo_prods = [r for r in results if r and r[0] == 'logo']
missing_prods = [r for r in results if r and r[0] == 'missing']

print(f"\n--- Products with Black Background / Rough Edges ({len(black_bg_prods)}) ---", flush=True)
for tag, pname, img, m in black_bg_prods:
    print(f"  {pname} -> {img} (edge mean {m:.1f})", flush=True)

print(f"\n--- Products with Logo Placeholders ({len(logo_prods)}) ---", flush=True)
for tag, pname, img, reason in logo_prods:
    print(f"  {pname} -> {img} ({reason})", flush=True)

print(f"\n--- Products with Missing Image Files ({len(missing_prods)}) ---", flush=True)
for tag, pname, img, reason in missing_prods:
    print(f"  {pname} -> {img}", flush=True)
