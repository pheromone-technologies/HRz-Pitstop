import os
import sys
import json
import re
import urllib.request
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"E:\coad\hrx website 2"
LOGO_FILE = r"E:\coad\tools for hrz\image logo editor\HRZ_BIKE_LOGO_page-0001-removebg-preview (3)_20250705_182254_0000.png"
HRZ_LOGO = Image.open(LOGO_FILE).convert('RGBA')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

with open(os.path.join(BASE_DIR, 'data', 'products.json'), 'r', encoding='utf-8') as f:
    products = json.load(f)

with open(os.path.join(BASE_DIR, 'tools', 'output', 'verified_images_checkpoint.json'), 'r', encoding='utf-8') as f:
    ckpt = json.load(f)

ckpt_by_name = { (v.get('product_name') or '').strip().lower(): v for v in ckpt.values() }

# Index raw disk files
print("Indexing raw disk files...")
raw_disk_index = {}
for root_dir in [os.path.join(BASE_DIR, 'images_processed', 'scraped'), os.path.join(BASE_DIR, 'images')]:
    if os.path.exists(root_dir):
        for root, _, files in os.walk(root_dir):
            for f in files:
                if f.lower().endswith(('.webp', '.jpg', '.png', '.jpeg')):
                    raw_disk_index[f.lower()] = os.path.join(root, f)
                    norm = re.sub(r'[^a-z0-9]', '', os.path.splitext(f)[0].lower())
                    if norm:
                        raw_disk_index[norm] = os.path.join(root, f)

print(f"Indexed {len(raw_disk_index)} raw disk keys.")

def watermark_and_compress(raw_im, dest_path, quality=90):
    im = raw_im.convert('RGBA')
    w, h = im.size
    
    # Scale watermark to ~15% of width
    scale_factor = 0.15
    padding = max(15, int(w * 0.02))
    
    wm_w = max(50, int(w * scale_factor))
    wm_ratio = wm_w / float(HRZ_LOGO.width)
    wm_h = int(HRZ_LOGO.height * wm_ratio)
    resized_logo = HRZ_LOGO.resize((wm_w, wm_h), Image.Resampling.LANCZOS)
    
    x = w - wm_w - padding
    y = h - wm_h - padding
    im.alpha_composite(resized_logo, dest=(x, y))
    
    final_rgb = im.convert('RGB')
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    final_rgb.save(dest_path, 'WEBP', quality=quality)

crash_prods = [p for p in products if (p.get('category') or '').lower() == 'crash protection']
print(f"Found {len(crash_prods)} Crash Protection products to process.")

processed = 0
failed = 0

for p in crash_prods:
    name = p['name'].strip().lower()
    entry = ckpt_by_name.get(name)
    target_rel = p.get('image', '').replace('\\', '/')
    if not target_rel:
        continue
    target_abs = os.path.join(BASE_DIR, target_rel.replace('/', os.sep))
    
    source = entry.get('source') if entry else None
    raw_img = None
    
    # 1. Local disk source
    if source and source.startswith('local_disk:'):
        fn = source.replace('local_disk:', '').strip().lower()
        src_path = raw_disk_index.get(fn)
        if not src_path:
            norm_fn = re.sub(r'[^a-z0-9]', '', os.path.splitext(fn)[0])
            src_path = raw_disk_index.get(norm_fn)
        if src_path and os.path.exists(src_path):
            try:
                raw_img = Image.open(src_path)
            except Exception:
                pass

    # 2. Direct URL source
    if raw_img is None and source and source.startswith(('url:', 'suggest_search:')):
        url = source.split(':', 1)[1].strip()
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                import io
                raw_img = Image.open(io.BytesIO(resp.read()))
        except Exception:
            pass

    # 3. Fallback: match name to raw disk files
    if raw_img is None:
        norm_name = re.sub(r'[^a-z0-9]', '', name)
        src_path = raw_disk_index.get(norm_name)
        if src_path and os.path.exists(src_path):
            try:
                raw_img = Image.open(src_path)
            except Exception:
                pass

    if raw_img is not None:
        try:
            watermark_and_compress(raw_img, target_abs, quality=90)
            processed += 1
            if processed % 10 == 0 or processed == len(crash_prods):
                print(f"Progress: {processed}/{len(crash_prods)} processed...")
        except Exception as e:
            failed += 1
    else:
        # If no raw source, keep existing file as-is
        pass

print(f"\nCompleted Crash Protection: {processed} reprocessed from raw (NO custom bg / NO rembg), {failed} errors.")

# Sync to test design site
with open(os.path.join(BASE_DIR, 'data', 'products.json'), 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

test_site_json = os.path.join(BASE_DIR, 'test design site', 'data', 'products.json')
if os.path.exists(test_site_json):
    with open(test_site_json, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
print("Synchronized products.json to storefronts.")
