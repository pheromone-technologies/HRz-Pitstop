import json
import os
import re

BASE_DIR = r"E:\coad\hrx website 2"
BIKES_JSON = os.path.join(BASE_DIR, "data", "bikes.json")
IMAGE_MAP_JS = os.path.join(BASE_DIR, "js", "image_map.js")

with open(IMAGE_MAP_JS, "r", encoding="utf-8") as f:
    c = f.read()

mapping = {}
for line in c.splitlines():
    m = re.search(r'"([^"]+)":\s*"([^"]+)"', line)
    if m:
        mapping[m.group(1)] = m.group(2)

with open(BIKES_JSON, "r", encoding="utf-8") as f:
    bikes = json.load(f)

updated = 0
for b in bikes:
    brand = b.get("brand", "")
    model = b.get("model", "")
    
    img = None
    for k in [model, f"{brand} {model}", f"{brand}_{model}"]:
        if k in mapping:
            img = mapping[k]
            break
            
    if not img:
        slug = f"{brand}_{model}".replace(" ", "_").replace("-", "_").replace("'", "").lower()
        for mk, mv in mapping.items():
            if slug in mv.lower():
                img = mv
                break
                
    if img:
        b["image"] = img.replace("_transparent.png", ".webp")
        b["transparentImage"] = img
        updated += 1
    else:
        if brand in mapping:
            b["image"] = mapping[brand].replace("_transparent.png", ".webp")
            b["transparentImage"] = mapping[brand]

with open(BIKES_JSON, "w", encoding="utf-8") as f:
    json.dump(bikes, f, indent=2)

print(f"Updated {updated}/{len(bikes)} motorcycles in data/bikes.json with exact actual image URLs.")
