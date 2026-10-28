import os

print("Searching for images with autowarrior or warrior or autologue:")
found = []
for root, dirs, files in os.walk('.'):
    for f in files:
        fl = f.lower()
        if any(k in fl for k in ['warrior', 'autowarrior', 'autologue']):
            found.append(os.path.join(root, f))

print(f"Total found: {len(found)}")
for f in found:
    print("  ", f)
