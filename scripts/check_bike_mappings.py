import json
import os
import re

BASE_DIR = r"E:\coad\hrx website 2"
image_map_file = os.path.join(BASE_DIR, "js", "image_map.js")

with open(image_map_file, encoding='utf-8') as f:
    txt = f.read()

mapping = {}
for line in txt.splitlines():
    m = re.search(r'"([^"]+)":\s*"([^"]+)"', line)
    if m:
        mapping[m.group(1)] = m.group(2)

print(f"Total mapped entries in js/image_map.js: {len(mapping)}")

# Check validity on disk
valid = 0
invalid = 0
for k, v in mapping.items():
    p = os.path.join(BASE_DIR, v.replace('/', os.sep))
    png_p = os.path.join(BASE_DIR, v.replace('.jpg', '_transparent.png').replace('/', os.sep))
    has_exact = os.path.exists(p)
    has_png = os.path.exists(png_p)
    if has_exact or has_png:
        valid += 1
    else:
        invalid += 1
        print(f"  MISSING ON DISK: {k:<25} -> {v} (png exists: {has_png})")

print(f"\nValid paths: {valid} | Missing paths: {invalid}")
