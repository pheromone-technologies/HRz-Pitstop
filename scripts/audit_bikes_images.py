import os
import sys

BASE_DIR = r"E:\coad\hrx website 2"
bikes_dir = os.path.join(BASE_DIR, "images", "bikes")
existing_files = os.listdir(bikes_dir) if os.path.exists(bikes_dir) else []
existing_lower = {f.lower(): f for f in existing_files}

models = [
    ('ROYAL ENFIELD', 'Himalayan 450'), ('ROYAL ENFIELD', 'Himalayan 411'), ('ROYAL ENFIELD', 'Classic 350 Reborn'),
    ('ROYAL ENFIELD', 'Hunter 350'), ('ROYAL ENFIELD', 'Meteor 350'), ('ROYAL ENFIELD', 'Guerrilla 450'),
    ('ROYAL ENFIELD', 'Interceptor 650'), ('ROYAL ENFIELD', 'Continental GT 650'), ('ROYAL ENFIELD', 'Super Meteor 650'),
    ('ROYAL ENFIELD', 'Bear 650'), ('ROYAL ENFIELD', 'Scram 411'), ('ROYAL ENFIELD', 'Scram 440'), ('ROYAL ENFIELD', 'Shotgun 650'),
    ('KTM', 'Duke 390 Gen-3'), ('KTM', 'Duke 250'), ('KTM', 'Duke 200'), ('KTM', 'Adventure 390'),
    ('KTM', 'Adventure 390 (2025)'), ('KTM', '390 Enduro R'), ('KTM', 'RC 390'), ('KTM', 'Adventure 250'),
    ('BAJAJ', 'Dominar 400'), ('BAJAJ', 'Pulsar NS400Z'), ('BAJAJ', 'Pulsar NS 200'), ('BAJAJ', 'Pulsar N250'), ('BAJAJ', 'Pulsar RS 200'),
    ('TRIUMPH', 'Speed 400'), ('TRIUMPH', 'Scrambler 400 X'), ('TRIUMPH', 'Tracker 400'), ('TRIUMPH', 'Tiger Sport 660'),
    ('TRIUMPH', 'Trident 660'), ('TRIUMPH', 'Speed T4'),
    ('YAMAHA', 'MT-15 V2'), ('YAMAHA', 'R15 V4'), ('YAMAHA', 'XSR 155'), ('YAMAHA', 'FZS V3 / V4'), ('YAMAHA', 'Aerox 155'), ('YAMAHA', 'NMAX 155'),
    ('HONDA', "H'ness CB 350"), ('HONDA', 'CB 350 RS'), ('HONDA', 'CB 200X'), ('HONDA', 'XL750 Transalp'), ('HONDA', 'NX500'),
    ('HERO', 'XPulse 200 4V'), ('HERO', 'XPulse 210'), ('HERO', 'Mavrick 440'),
    ('TVS', 'Apache RR 310'), ('TVS', 'Apache RTR 310'), ('TVS', 'Apache RTX 300'), ('TVS', 'Ronin 225'),
    ('HARLEY DAVIDSON', 'X440'), ('HARLEY DAVIDSON', 'Pan America'),
    ('SUZUKI', 'V-Strom SX 250'), ('SUZUKI', 'V-Strom 800DE'), ('SUZUKI', 'Gixxer 250'),
    ('BMW', 'G 310 GS'), ('BMW', 'F 450 GS'), ('BMW', 'G 310 R'), ('BMW', 'S 1000 RR'), ('BMW', 'F 850 GS'),
    ('KAWASAKI', 'KLX 230'), ('KAWASAKI', 'Ninja 300'), ('KAWASAKI', 'Z900'),
    ('YEZDI', 'Adventure'), ('YEZDI', 'Scrambler'), ('YEZDI', 'Roadster'),
    ('APRILIA', 'RS 457'), ('APRILIA', 'Tuono 457'), ('APRILIA', 'Tuareg 660')
]

print(f"Total models to check: {len(models)}")
found_transparent = []
found_jpg_only = []
missing = []

for make, model in models:
    # Look for transparent png first, then jpg/webp
    clean_m = model.replace(' ', '_').replace('-', '_').replace("'", "").replace('(', '').replace(')', '').lower()
    clean_mk = make.replace(' ', '_').replace('-', '_').lower()
    
    # Try combinations
    cand_png = f"{clean_mk}_{clean_m}_transparent.png"
    cand_jpg = f"{clean_mk}_{clean_m}.jpg"
    cand_png2 = f"{clean_m}_transparent.png"
    cand_jpg2 = f"{clean_m}.jpg"
    
    matched = None
    for cand in [cand_png, cand_png2]:
        if cand in existing_lower:
            matched = existing_lower[cand]
            found_transparent.append((make, model, matched))
            break
            
    if not matched:
        for cand in [cand_jpg, cand_jpg2]:
            if cand in existing_lower:
                matched = existing_lower[cand]
                found_jpg_only.append((make, model, matched))
                break
                
    if not matched:
        # Check partial
        for f in existing_files:
            fl = f.lower()
            if clean_m in fl:
                matched = f
                if '_transparent.png' in fl:
                    found_transparent.append((make, model, matched))
                else:
                    found_jpg_only.append((make, model, matched))
                break
                
    if not matched:
        missing.append((make, model))

print(f"Found Transparent PNG: {len(found_transparent)}")
print(f"Found JPG Only:        {len(found_jpg_only)}")
print(f"Missing Any Image:     {len(missing)}")

print("\n--- MISSING BIKES ---")
for mk, md in missing:
    print(f"  {mk:<18} : {md}")

print("\n--- JPG ONLY (NEEDS TRANSPARENT PNG) ---")
for mk, md, f in found_jpg_only:
    print(f"  {mk:<18} : {md:<22} -> {f}")
