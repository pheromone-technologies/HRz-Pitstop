import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('tools/output/verified_images_checkpoint.json', encoding='utf-8') as f:
    ckpt = json.load(f)

count = 0
for k, v in ckpt.items():
    name = (v.get('product_name') or '').lower()
    if any(w in name for w in ['crash', 'guard', 'bash', 'saddle', 'slider', 'radiator', 'carrier', 'mount', 'stand']):
        count += 1
        if count <= 15:
            print(f"Product: {v.get('product_name')}")
            print(f"  Target: {v.get('image_path')}")
            print(f"  Source: {v.get('source')}")
            print("-" * 50)

print(f"\nTotal bike accessory products found: {count}")
