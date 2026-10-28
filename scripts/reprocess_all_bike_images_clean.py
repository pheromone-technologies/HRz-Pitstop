import os
import sys
import json
import re
import socket
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
socket.setdefaulttimeout(10)

BASE_DIR = r"E:\coad\hrx website 2"
LOGO_FILE = r"E:\coad\tools for hrz\image logo editor\HRZ_BIKE_LOGO_page-0001-removebg-preview (3)_20250705_182254_0000.png"
HRZ_LOGO = Image.open(LOGO_FILE).convert('RGBA')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# 1. Load data
with open(os.path.join(BASE_DIR, 'data', 'products.json'), 'r', encoding='utf-8') as f:
    products = json.load(f)

with open(os.path.join(BASE_DIR, 'tools', 'output', 'verified_images_checkpoint.json'), 'r', encoding='utf-8') as f:
    ckpt = json.load(f)

# Build clean lookup table for checkpoint
ckpt_by_clean = {}
for k, v in ckpt.items():
    raw_name = (v.get('product_name') or '').lower()
    c = re.sub(r'[^a-z0-9]', '', raw_name)
    if c and c not in ckpt_by_clean:
        ckpt_by_clean[c] = v

# 2. Index raw disk files across scraped cache and images
print("Indexing raw disk files across images_processed/scraped and images/...")
raw_disk_index = {}
scan_dirs = [
    os.path.join(BASE_DIR, 'images_processed', 'scraped'),
    os.path.join(BASE_DIR, 'images')
]

for sdir in scan_dirs:
    if os.path.exists(sdir):
        for root, _, files in os.walk(sdir):
            for f in files:
                if f.lower().endswith(('.webp', '.jpg', '.png', '.jpeg')):
                    fl = f.lower()
                    if fl not in raw_disk_index:
                        raw_disk_index[fl] = os.path.join(root, f)
                    norm = re.sub(r'[^a-z0-9]', '', os.path.splitext(f)[0].lower())
                    if norm and norm not in raw_disk_index:
                        raw_disk_index[norm] = os.path.join(root, f)

print(f"Indexed {len(raw_disk_index)} raw disk keys.")

def watermark_and_compress(raw_im, dest_path, quality=88):
    im = raw_im.convert('RGBA')
    w, h = im.size
    
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

# 3. Identify all bike accessory products
bike_categories = [
    'crash protection',
    'luggage & storage',
    'body parts & panels',
    'mirrors & handlebar accessories',
    'exhaust system',
    'lighting & electrical'
]

bike_keywords = [
    'crash', 'guard', 'bash', 'plate', 'saddle', 'stay', 'radiator', 'grill',
    'carrier', 'slider', 'stand', 'gps', 'mount', 'handle', 'bar', 'riser',
    'footrest', 'oil cap', 'visor', 'tail tidy', 'exhaust', 'fluid cap',
    'boot guard', 'hugger', 'lever', 'master cylinder'
]

targets = []
for p in products:
    name = (p.get('name') or '').lower()
    cat = (p.get('category') or '').lower()
    if cat in bike_categories or any(k in name for k in bike_keywords):
        targets.append(p)

print(f"Found {len(targets)} total bike accessory products to verify and remediate.")

def get_raw_image(p):
    name = p['name'].strip().lower()
    clean_name = re.sub(r'[^a-z0-9]', '', name)
    
    # Check checkpoint entry
    entry = ckpt_by_clean.get(clean_name)
    if not entry:
        for ck, cv in ckpt_by_clean.items():
            if (len(clean_name) > 12 and clean_name in ck) or (len(ck) > 12 and ck in clean_name):
                entry = cv
                break
                
    source = entry.get('source') if entry else None
    
    # Strategy 1: local_disk source
    if source and source.startswith('local_disk:'):
        fn = source.replace('local_disk:', '').strip().lower()
        src_path = raw_disk_index.get(fn)
        if not src_path:
            norm_fn = re.sub(r'[^a-z0-9]', '', os.path.splitext(fn)[0])
            src_path = raw_disk_index.get(norm_fn)
        if src_path and os.path.exists(src_path):
            try:
                return Image.open(src_path)
            except Exception:
                pass

    # Strategy 2: URL source
    if source and source.startswith(('url:', 'suggest_search:')):
        url = source.split(':', 1)[1].strip()
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                import io
                return Image.open(io.BytesIO(resp.read()))
        except Exception:
            pass

    # Strategy 3: match name against raw disk index
    src_path = raw_disk_index.get(clean_name)
    if src_path and os.path.exists(src_path):
        try:
            return Image.open(src_path)
        except Exception:
            pass
            
    return None

def process_product(p):
    pid = p.get('id')
    target_rel = (p.get('image') or '').replace('\\', '/')
    if not target_rel:
        return pid, False, "No image path"
        
    target_abs = os.path.join(BASE_DIR, target_rel.replace('/', os.sep))
    raw_im = get_raw_image(p)
    if raw_im is None:
        return pid, False, "No raw source found"
        
    try:
        watermark_and_compress(raw_im, target_abs, quality=88)
        return pid, True, "Success"
    except Exception as e:
        return pid, False, str(e)

print(f"Beginning multi-threaded processing for {len(targets)} bike products...")
success_count = 0
fail_count = 0

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(process_product, p): p for p in targets}
    for i, fut in enumerate(as_completed(futures), 1):
        pid, ok, msg = fut.result()
        if ok:
            success_count += 1
        else:
            fail_count += 1
        if i % 50 == 0 or i == len(targets):
            print(f"[{i}/{len(targets)}] Completed: {success_count} success, {fail_count} skipped/failed")

print(f"\nFinal Summary: {success_count} bike images refreshed from raw (KEEPING BIKE AS-IS, NO CUSTOM BG, NO REMBG).")

# Sync data/products.json and test design site
with open(os.path.join(BASE_DIR, 'data', 'products.json'), 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

test_site_json = os.path.join(BASE_DIR, 'test design site', 'data', 'products.json')
if os.path.exists(test_site_json):
    with open(test_site_json, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

print("Saved data/products.json and synchronized test design site.")
