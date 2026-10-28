import os
import sys
import json
import re

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Index all available images on disk across images/ and images_processed/scraped/
disk_images = []
for root, _, files in os.walk('images'):
    for f in files:
        if f.lower().endswith(('.webp', '.png', '.jpg', '.jpeg')):
            disk_images.append((f, os.path.join(root, f).replace('\\', '/')))

for root, _, files in os.walk('images_processed/scraped'):
    for f in files:
        if f.lower().endswith(('.webp', '.png', '.jpg', '.jpeg')):
            disk_images.append((f, os.path.join(root, f).replace('\\', '/')))

print(f"Total disk candidate images indexed: {len(disk_images)}")

def find_best_image(name, brand=""):
    # Tokenize name
    # Ignore brand, numbers like 1, 2, filler words
    stop = {'black', 'white', 'red', 'blue', 'grey', 'yellow', 'l', 'm', 'xl', '2xl', '3xl', 'set', 'edition', 'decor', 'f/f', 'd/v', 'decor', 'decora'}
    words = [w for w in re.split(r'[^a-zA-Z0-9]+', name.lower()) if len(w) > 2 and w not in stop]
    
    candidates = []
    for fname, fpath in disk_images:
        fn_l = fname.lower()
        # Exclude known bad logos/banners
        if any(bad in fn_l for bad in ['logo', 'banner', 'youtube', 'autowarrior', 'autonity', 'a.webp', 'social_share', 'motodrift', 'bkwgears', 'page_logo']):
            continue
            
        score = 0
        for w in words:
            if w in fn_l:
                score += 1
                
        if score >= 2:
            candidates.append((score, fpath))
            
    candidates.sort(key=lambda x: -x[0])
    return [c[1] for c in candidates[:5]]

# Test key products
test_items = [
    'CARBONADO Y07 ULTIMATE HYDRATION BACK PACK BLUE',
    'OGIO BACK PACK',
    'NORIFUMI NOCTUS T5 CRF 150L +DB',
    'AXOR RIDER JACKET DRIFT',
    'APOLLO 90/90-21 54H TRAMPLR XR TL',
    '66 BHP CHAIN LUB',
    '66 BHP HAND SLEEVE',
    '66BHP-MICRO FIBER CLOTH 250GSM RED',
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
    'STUDDS F/F DRIFTER DECOR',
    'STUDDS F/F DRIFTTER DECOR',
    'TRYKA-HELMET BAG',
    'VEGA BALCLAVAA',
    'VIATERRA - 100% WP LEH SADDLE BAG',
    'LCB ADV390 BELLATOR LOWER CRASHGUARD BLACK',
    'LCB ADV390 RAPTOR UPPER CRASHGUARD BLACK',
    'LCB HIMALAYA 450 BOLIDE PILLION FOOTREST',
    'LCB HIMALAYAN REAR BREAK FLUID CAP SS',
    'LCB HNESS SPYRO REAR BREAK FLUID CAP',
    'Givi Matterhorn Aluminium Top Case 47ltrs Plate Chr (MTN47A(WP))',
    'Givi-43ltr Mulebox Monolock TopcaseBlk (Tech) ( E43NTL)',
    'CARBONADO QUENCH HYDRATION BLADDER 2.5L',
    'CRAMSTER STALLION SADDLE BAG - BLACK - 60L',
    'LCB TRIUMPH SPEED 400 CARRIER PLATE',
    'MT - HONDA H\'NESS 350 BACK CARRIER',
    'MT - HONDA H\'NESS 350 ENGINE GAURD',
    'LCB YAMAHA XSR 155 AERO SHORT VISOR BLK SILVER',
    'RRP RUMBLER ACE EXHAUST UNIBODY BLACK',
    'FLASH X JAWA 42',
    'FLASH X SCRAM 411',
    'FLASH X HAZARD YAMAHA FZS',
    'FLASH X HAZARD KTM DUKE 200 BS6',
    'SCALA KNEEGUARD'
]

print("\n--- MATCHING RESULTS ---")
for item in test_items:
    matches = find_best_image(item)
    print(f"\nTarget: {item}")
    if matches:
        for m in matches[:3]:
            print(f"  -> {m}")
    else:
        print("  -> NO MATCH")
