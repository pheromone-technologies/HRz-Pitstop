import json
import os
import sys
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

print("Starting Image Audit & Fix...", flush=True)

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print(f"Loaded {len(products)} products.", flush=True)

def analyze_image(path):
    if not path or not os.path.exists(path):
        return None
    try:
        with Image.open(path) as im:
            rgb = im.convert('RGB').resize((64, 64))
            arr = np.asarray(rgb)
            mean_val = float(arr.mean())
            std_val = float(arr.std())
            dark_pct = float((arr < 45).all(axis=2).mean() * 100)
            white_pct = float((arr > 235).all(axis=2).mean() * 100)
            
            # Bad if bleached ghost:
            is_ghost = (white_pct > 70 and dark_pct < 0.8) or (mean_val > 210 and dark_pct < 0.5) or (std_val < 30 and white_pct > 60)
            return {
                'path': path,
                'mean': mean_val,
                'std': std_val,
                'dark_pct': dark_pct,
                'white_pct': white_pct,
                'is_ghost': is_ghost
            }
    except Exception as e:
        return None

# Step 1: Scan all products
bad_products = []
for p in products:
    stat = analyze_image(p.get('image'))
    if stat and stat['is_ghost']:
        bad_products.append((p, stat))

print(f"Found {len(bad_products)} products with washed-out/ghost primary images.", flush=True)

# Step 2: Fix from gallery
fixed_from_gallery = 0
unfixed = []

for p, stat in bad_products:
    gallery = p.get('gallery', [])
    good_cand = None
    best_dark = 0.0
    
    for g in gallery:
        if g == p['image']: continue
        g_stat = analyze_image(g)
        if g_stat and not g_stat['is_ghost']:
            if g_stat['dark_pct'] > best_dark:
                best_dark = g_stat['dark_pct']
                good_cand = g
                
    if good_cand:
        old_img = p['image']
        p['image'] = good_cand
        # move old_img to end of gallery
        p['gallery'] = [good_cand] + [x for x in gallery if x != good_cand and x != old_img]
        fixed_from_gallery += 1
    else:
        unfixed.append((p, stat))

print(f"Fixed from existing gallery: {fixed_from_gallery}", flush=True)
print(f"Remaining to search on disk: {len(unfixed)}", flush=True)

# Step 3: Index scraped / raw images
print("Indexing raw and scraped images...", flush=True)
scraped_index = {}
search_dirs = [
    'images_processed/scraped',
    'images_processed/inventory_sync_multisite',
    'images_processed/inventory_sync_fuzzy',
    'images'
]

for sdir in search_dirs:
    if os.path.exists(sdir):
        for root, dirs, files in os.walk(sdir):
            for f in files:
                if f.endswith(('.webp', '.jpg', '.png')):
                    # clean key
                    k = f.lower().replace('-', '_').replace(' ', '_').replace('.webp', '').replace('.jpg', '').replace('.png', '')
                    scraped_index[k] = os.path.join(root, f)

print(f"Indexed {len(scraped_index)} files.", flush=True)

fixed_from_disk = 0
still_unfixed = []

for p, stat in unfixed:
    base = os.path.basename(stat['path']).lower().replace('.webp', '').replace('.jpg', '').replace('.png', '').replace('-', '_').replace(' ', '_')
    # strip trailing _1, _2
    clean_base = base.rsplit('_', 1)[0] if (base.endswith('_1') or base.endswith('_2') or base.endswith('_3')) else base
    
    found = None
    for k, fpath in scraped_index.items():
        if clean_base in k or k in clean_base:
            c_stat = analyze_image(fpath)
            if c_stat and not c_stat['is_ghost']:
                found = fpath
                break
                
    if found:
        rel_path = found.replace('\\', '/')
        if rel_path.startswith('./'): rel_path = rel_path[2:]
        p['image'] = rel_path
        if 'gallery' not in p or not p['gallery']:
            p['gallery'] = [rel_path]
        else:
            p['gallery'] = [rel_path] + [x for x in p['gallery'] if x != rel_path]
        fixed_from_disk += 1
    else:
        still_unfixed.append(p)

print(f"Fixed from disk search: {fixed_from_disk}", flush=True)
print(f"Still unresolved: {len(still_unfixed)}", flush=True)

# Save updated products.json
with open('data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

# Also update test design site if present
if os.path.exists('test design site/data/products.json'):
    with open('test design site/data/products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

print("Saved updated data/products.json!", flush=True)

# Test the specific items from the screenshot
print("\n--- Verification of Screenshot Products ---", flush=True)
for pid in ['hrz-moto-torque-guerrilla-crash-guard-1869', 'hrz-moto-torque-dominar-crash-guard-1892', 'hrz-moto-torque-h-ness-350-rs-crash-guard-1904']:
    p = next((x for x in products if x['id'] == pid), None)
    if p:
        s = analyze_image(p['image'])
        print(f"{p['name']} -> {p['image']} (dark={s['dark_pct']:.1f}%, is_ghost={s['is_ghost']})", flush=True)
