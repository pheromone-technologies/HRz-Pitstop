import re
import os

with open('js/image_map.js', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
valid = 0
missing = []
updated = {}

for line in lines:
    m = re.match(r'\s*"([^"]+)"\s*:\s*"([^"]+)"', line)
    if m:
        key, path = m.group(1), m.group(2)
        trans_path = path.replace('.jpg', '_transparent.png').replace('.webp', '_transparent.png')
        if os.path.exists(trans_path):
            updated[key] = trans_path.replace('\\', '/')
            valid += 1
        elif os.path.exists(path):
            updated[key] = path.replace('\\', '/')
            valid += 1
        else:
            missing.append((key, path, trans_path))

trans_count = sum(1 for p in updated.values() if p.endswith('_transparent.png'))
print(f"Total evaluated: {len(updated) + len(missing)}")
print(f"Valid on disk: {valid}")
print(f"Transparent PNGs: {trans_count} / {len(updated)}")
print(f"Missing count: {len(missing)}")

# Write clean map to js/image_map.js
with open('js/image_map.js', 'w', encoding='utf-8') as f:
    f.write('window.HRzImageMap = {\n')
    for k, v in updated.items():
        f.write(f'  "{k}": "{v}",\n')
    f.write('};\n')
print("Successfully refreshed js/image_map.js with direct transparent links!")

