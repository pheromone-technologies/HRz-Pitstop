import json
import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/bad_images_summary.json', encoding='utf-8') as f:
    bad_items = json.load(f)

print(f"Total bad items: {len(bad_items)}")

found_alternatives = {}

for pid, info in bad_items.items():
    name = info['name']
    path = info['path']
    basename = os.path.basename(path).replace('.webp', '')
    
    # search across images_processed
    candidates = []
    for root, dirs, files in os.walk('images_processed'):
        if 'catalog' in root: continue # avoid the broken ones
        for f in files:
            f_low = f.lower()
            if basename in f_low or any(w in f_low for w in name.lower().split() if len(w) > 4):
                full_c = os.path.join(root, f)
                # check if valid size > 5KB
                if os.path.getsize(full_c) > 6000:
                    candidates.append(full_c)
    
    if candidates:
        found_alternatives[pid] = candidates

print(f"Found clean alternatives for {len(found_alternatives)} of {len(bad_items)} bad items!")
for pid, cands in list(found_alternatives.items())[:10]:
    print(f"\n{bad_items[pid]['name']}:")
    print(f"   Current bad: {bad_items[pid]['path']}")
    print(f"   Candidate clean: {cands[0]}")
