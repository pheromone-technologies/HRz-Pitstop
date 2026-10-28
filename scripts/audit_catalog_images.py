import json
import os
import hashlib
from PIL import Image
import numpy as np

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print(f"Total products: {len(products)}")

# 1. Check duplicate image hashes across products
hash_to_products = {}
missing_files = []
pillarbox_candidates = []

for p in products:
    img_path = p.get('image')
    if not img_path:
        continue
    if not os.path.exists(img_path):
        missing_files.append((p.get('id'), p.get('name'), img_path))
        continue
        
    try:
        data = open(img_path, 'rb').read()
        h = hashlib.md5(data).hexdigest()
        hash_to_products.setdefault(h, []).append(p)
        
        # Check aspect ratio
        im = Image.open(img_path)
        w, h_dim = im.size
        ratio = w / h_dim
        if ratio < 0.85 or ratio > 1.15:
            pillarbox_candidates.append((p.get('id'), p.get('name'), img_path, w, h_dim, round(ratio, 2)))
    except Exception as e:
        pass

print(f"Missing image files: {len(missing_files)}")
print(f"Images with non-square aspect ratio (<0.85 or >1.15): {len(pillarbox_candidates)}")

print("\n--- Duplicate image hashes shared by > 2 distinct products ---")
duplicate_groups = 0
for h, plist in hash_to_products.items():
    if len(plist) > 2:
        duplicate_groups += 1
        print(f"\nHash {h[:10]} ({len(plist)} products): {plist[0].get('image')}")
        for p in plist[:5]:
            print(f"   [{p.get('id')}] {p.get('name')}")
        if len(plist) > 5:
            print(f"   ... and {len(plist) - 5} more")

print(f"\nTotal duplicate groups (>2 products): {duplicate_groups}")
