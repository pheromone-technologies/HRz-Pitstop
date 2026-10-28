import os
import json
import re

# Load products from data/products.json
with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

# Index all files in images/ and images_processed/
disk_files = []
for root, _, files in os.walk('images'):
    for f in files:
        if f.lower().endswith(('.webp', '.png', '.jpg', '.jpeg')):
            disk_files.append((f, os.path.join(root, f).replace('\\', '/')))

for root, _, files in os.walk('images_processed/scraped'):
    for f in files:
        if f.lower().endswith(('.webp', '.png', '.jpg', '.jpeg')):
            disk_files.append((f, os.path.join(root, f).replace('\\', '/')))

print(f"Total disk candidate images indexed: {len(disk_files)}")

# Check each known bad product
target_names = [
    'CARBONADO Y07 ULTIMATE HYDRATION BACK PACK BLUE',
    'OGIO BACK PACK',
    'NORIFUMI NOCTUS T5 CRF 150L +DB',
    'LEVER GUARD BSDDP ADJ',
    'MT - HIM 450 GPS MOUNT',
    'MT - HIM 450 HANDLEBAR RISERS',
    'MT - HIM 450 REAR MASTER CYL GUARD (SS)',
    'MT - HIMALAYAN 450 - GPS MOUNT',
    'MT - HIMALAYAN 450 FRONT MASTER CYLINDER GUARD BLACK',
    'MT - HIMALAYAN GPS MOUNT',
    'MT - PULSAR NS 200 CRASH GUARD',
    'MT- TRIUMPH FOOT REST',
    'MT-HIMALAYAN 450 RADIATOR GUARD-BLACK',
    'MT-HIMALAYAN 450 RESERVOIR OIL GUARD BLACK',
    'RAIDA - TRAILCRAFT HANDLEBAR BAG',
    'SMK OUTER VISOR STELLAR CLEAR/TINTED',
    'SMK STELLAR SPORTS FLIGHT GL213 L',
    'SMK TYPHOON SPARKO GL266 L',
    'STUDDS F/F DRIFTER DECOR',
    'STUDDS F/F RAIDER SUPER DECOR',
    'TRYKA-HELMET BAG',
    'TT REVO FLUX M',
    'TT REVO GEAR BLACK RED L',
    'TT REVO GRAND PRIX WHITE LIGHT BLUE L',
    'TT REVO LEOPARD INDIA EDITION L',
    'TT REVO OVERTECH BLACK ORANGE M',
    'TT REVO SUSHI TIME L',
    'TT REVO TOURIST RED FLUO L',
    'VEGA BALCLAVAA',
    'VIATERRA - 100% WP LEH SADDLE BAG'
]

for tname in target_names:
    tokens = [w for w in re.split(r'[^a-zA-Z0-9]+', tname.lower()) if len(w) > 2 and w not in ['black', 'blue', 'red', 'white', 'rear', 'front', 'set', 'edition']]
    matches = []
    for fname, fpath in disk_files:
        fn_l = fname.lower()
        if 'logo' in fn_l or 'banner' in fn_l:
            continue
        # Count token matches
        score = sum(1 for tok in tokens if tok in fn_l)
        if score >= min(3, len(tokens)):
            matches.append((score, fpath))
    matches.sort(key=lambda x: -x[0])
    print(f"\nTarget: {tname}")
    if matches:
        for m in matches[:3]:
            print(f"  Match (score {m[0]}): {m[1]}")
    else:
        print("  NO direct disk match found")
