import os
from PIL import Image

# Search through all processed images
print("Searching for images in images_processed and images:")
candidates = []
for root, dirs, files in os.walk('.'):
    if any(k in root for k in ['.git', '.venv', '_vault_archive']):
        continue
    for f in files:
        if f.endswith(('.webp', '.png', '.jpg')):
            full = os.path.join(root, f)
            fl = f.lower()
            if any(k in fl for k in ['autowarrior', 'warrior', 'logo', 'autologue']):
                candidates.append(full)

print(f"Direct filename matches: {len(candidates)}")
for c in candidates:
    print("  ", c)

# Let's inspect the images of the autowarrior links products:
test_paths = [
    'images_processed/catalog/unbranded/jb_racing_body_cover_elastic_blk_1.webp',
    'images_processed/catalog/jawa/flash_x_jawa_classic_1.webp',
    'images_processed/catalog/bajaj/flash_x_hazard_bajaj_pulsar_220_2.webp',
    'images_processed/catalog/race_dynamics/hazard_light_x_flash_1.webp',
    'images_processed/catalog/raida/raida_-_base_layer_black_top_m_1.webp'
]

for p in test_paths:
    if os.path.exists(p):
        try:
            im = Image.open(p)
            print(f"Path: {p} | Size: {im.size} | Mode: {im.mode}")
        except Exception as e:
            print(f"Path: {p} | Error: {e}")
