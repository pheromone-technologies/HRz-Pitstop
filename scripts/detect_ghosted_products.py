import json
import os
import glob
import re
from PIL import Image
import numpy as np

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

with open('tools/output/verified_images_checkpoint.json', 'r', encoding='utf-8') as f:
    ckpt = json.load(f)

print(f"Products: {len(products)}, Checkpoint: {len(ckpt)}")

# Build raw disk index
raw_disk_index = {}
for root_dir in ['images_processed/scraped', 'images', '_vault_archive']:
    if os.path.exists(root_dir):
        for root, _, files in os.walk(root_dir):
            for f in files:
                if f.lower().endswith(('.webp', '.jpg', '.png', '.jpeg')):
                    raw_disk_index[f.lower()] = os.path.join(root, f)
                    norm = re.sub(r'[^a-z0-9]', '', os.path.splitext(f)[0].lower())
                    if norm:
                        raw_disk_index[norm] = os.path.join(root, f)

# Find all products in catalog where rembg created white hazy ghosting
ghosted_products = []

for p in products:
    img_path = p.get('image', '').replace('\\', '/')
    if not img_path or not os.path.exists(img_path):
        continue
    
    # Check if this image has characteristics of rembg ghosting
    # rembg ghosting has: pure white background pixels (255, 255, 255) around the edges,
    # but transitional translucent white haze (RGB 230-254) across large patches where the bike was erased.
    try:
        im = Image.open(img_path).convert('RGB')
        arr = np.array(im)
        h, w, _ = arr.shape
        
        # Check border purity
        borders = np.vstack([arr[:10, :, :].reshape(-1, 3), arr[-10:, :, :].reshape(-1, 3),
                             arr[:, :10, :].reshape(-1, 3), arr[:, -10:, :].reshape(-1, 3)])
        white_borders = np.all(borders == 255, axis=1)
        border_white_pct = np.mean(white_borders) * 100
        
        # Check hazy pixels: RGB between 225 and 250 with low saturation (std < 10)
        max_c = np.max(arr, axis=2)
        min_c = np.min(arr, axis=2)
        mean_c = np.mean(arr, axis=2)
        hazy_mask = (mean_c >= 225) & (mean_c <= 252) & ((max_c - min_c) < 15)
        hazy_pct = np.mean(hazy_mask) * 100
        
        # Check dark product pixels
        dark_mask = mean_c < 70
        dark_pct = np.mean(dark_mask) * 100
        
        # If it has white borders and significant hazy pixels, it was ghosted by rembg!
        name = p.get('name', '').lower()
        cat = p.get('category', '').lower()
        is_bike_accessory = any(k in name for k in [
            'crash', 'guard', 'bash', 'plate', 'saddle', 'stay', 'radiator', 'grill',
            'carrier', 'slider', 'stand', 'gps', 'mount', 'handle', 'bar', 'riser',
            'footrest', 'oil cap', 'visor', 'tail tidy', 'exhaust', 'fluid cap',
            'boot guard', 'hugger', 'paddock', 'lever', 'master cylinder', 'brake'
        ]) or cat in ['crash protection', 'luggage & storage', 'body parts & panels', 'mirrors & handlebar accessories', 'exhaust systems']
        
        if is_bike_accessory and border_white_pct > 80 and hazy_pct > 8:
            ghosted_products.append({
                'id': p.get('id'),
                'name': p.get('name'),
                'image': img_path,
                'border_white_pct': round(border_white_pct, 1),
                'hazy_pct': round(hazy_pct, 1),
                'dark_pct': round(dark_pct, 1)
            })
    except Exception as e:
        pass

print(f"\nDetected {len(ghosted_products)} bike products with rembg ghosting artifacts:")
for gp in ghosted_products[:20]:
    print(f"  [{gp['id']}] {gp['name']} (haze={gp['hazy_pct']}%, dark={gp['dark_pct']}%)")
