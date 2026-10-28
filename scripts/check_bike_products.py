import os
import json
import glob
from PIL import Image
import numpy as np

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

with open('tools/output/verified_images_checkpoint.json', 'r', encoding='utf-8') as f:
    ckpt = json.load(f)

print(f"Total products in products.json: {len(products)}")
print(f"Total items in checkpoint: {len(ckpt)}")

# Build mapping of target image_path -> checkpoint entry
ckpt_by_target = {}
for k, v in ckpt.items():
    target = v.get('image_path')
    if target:
        ckpt_by_target[target.replace('\\', '/')] = v

matched_count = 0
bike_keyword_count = 0

for p in products:
    img = (p.get('image') or '').replace('\\', '/')
    name = (p.get('name') or '').lower()
    cat = (p.get('category') or '').lower()
    
    is_bike_part = any(w in name for w in [
        'crash guard', 'crashguard', 'bash plate', 'bashplate', 'saddle stay', 'saddlestay',
        'radiator grill', 'headlight grill', 'carrier plate', 'carrier', 'slider',
        'side stand', 'gps mount', 'handle bar', 'handlebar', 'footrest', 'oil cap',
        'visor', 'tail tidy', 'exhaust', 'fluid cap', 'boot guard', 'brake fluid'
    ]) or cat in ['crash protection', 'luggage & storage', 'body parts & panels', 'mirrors & handlebar accessories', 'exhaust systems']
    
    if is_bike_part:
        bike_keyword_count += 1
        if img in ckpt_by_target:
            matched_count += 1

print(f"Products identified as bike accessories: {bike_keyword_count}")
print(f"Matched in checkpoint: {matched_count}")
