import json
import os
import re

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

with open('tools/output/verified_images_checkpoint.json', 'r', encoding='utf-8') as f:
    ckpt = json.load(f)

# Index raw files across the workspace
print("Indexing raw disk files...")
raw_disk_files = {}
for root_dir in ['images_processed/scraped', 'images', '_vault_archive']:
    if os.path.exists(root_dir):
        for root, _, files in os.walk(root_dir):
            for f in files:
                if f.lower().endswith(('.webp', '.jpg', '.png', '.jpeg')):
                    raw_disk_files[f.lower()] = os.path.join(root, f)
                    # Also index normalized
                    norm = re.sub(r'[^a-z0-9]', '', os.path.splitext(f)[0].lower())
                    if norm:
                        raw_disk_files[norm] = os.path.join(root, f)

print(f"Total raw disk keys indexed: {len(raw_disk_files)}")

# Checkpoint map
ckpt_by_name = {}
for k, v in ckpt.items():
    pname = (v.get('product_name') or '').strip().lower()
    if pname:
        ckpt_by_name[pname] = v

bike_keywords = [
    'crash', 'guard', 'bash', 'plate', 'saddle', 'stay', 'radiator', 'grill',
    'carrier', 'slider', 'stand', 'gps', 'mount', 'handle', 'bar', 'riser',
    'footrest', 'oil cap', 'visor', 'tail tidy', 'exhaust', 'fluid cap',
    'boot guard', 'hugger', 'paddock', 'lever', 'master cylinder', 'brake'
]

bike_categories = [
    'crash protection', 'luggage & storage', 'body parts & panels',
    'mirrors & handlebar accessories', 'exhaust systems'
]

bike_products = []
for p in products:
    name = (p.get('name') or '').lower()
    cat = (p.get('category') or '').lower()
    is_bike = any(k in name for k in bike_keywords) or cat in bike_categories
    if is_bike:
        bike_products.append(p)

print(f"Total bike products in catalog: {len(bike_products)}")

found_source_disk = 0
found_source_url = 0
missing_source = 0

for p in bike_products:
    name = p.get('name', '').strip().lower()
    entry = ckpt_by_name.get(name)
    source = entry.get('source') if entry else None
    
    if source:
        if source.startswith('local_disk:'):
            fn = source.replace('local_disk:', '').strip().lower()
            if fn in raw_disk_files:
                found_source_disk += 1
            else:
                missing_source += 1
        elif source.startswith(('url:', 'suggest_search:')):
            found_source_url += 1
        else:
            missing_source += 1
    else:
        # Check if name matches directly in raw_disk_files
        norm_name = re.sub(r'[^a-z0-9]', '', name)
        if norm_name in raw_disk_files:
            found_source_disk += 1
        else:
            missing_source += 1

print(f"Found on local disk: {found_source_disk}")
print(f"Found via URL: {found_source_url}")
print(f"Missing source: {missing_source}")
