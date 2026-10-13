import os
import json
import difflib

brands_models = {
    "ROYAL ENFIELD": [
    "Scram 440 new", "Classic 650", "Bear 650", "Guerrilla 450", 
    "Himalayan 450", "SUPER METEOR 650", "Hunter 350", "Himalayan", 
    "Classic 350 Reborn", "Standard 350 Reborn", "Meteor 350", "Classic", 
    "Standard", "Electra", "Interceptor", "Thunderbird", "Thunderbird X", 
    "Continental GT", "Scram"
    ],
    "YAMAHA": [
    "XSR 155", "RX 100", "Aerox 155", "MT 15", "R3", "R15 V1", 
    "R15 V2", "R15 V3", "R15 V4", "R1"
    ],
    "KTM": [
    "KTM 390 Enduro R", "Adventure 890", "ADVENTURE 390 2025 Model", 
    "Adventure 390", "Duke 125", "Duke 200", "Duke 250 BS6", "Duke 250", 
    "Duke 390", "RC 390"
    ],
    "BAJAJ": [
    "NS400Z", "Pulsar 220", "Pulsar NS 200", "Pulsar RS 200", 
    "Dominar 400", "Pulsar 150", "Pulsar 180"
    ],
    "HONDA": [
    "XL750 Transalp", "NX500", "CB 200X", "Hness CB 350", "Hornet 160R", 
    "CBR 250 R", "CB 300", "CB 350 RS", "CB 500X", "NX400", "CB650R", 
    "CBR 650R", "CBR 1000RR"
    ],
    "SUZUKI": [
    "Gixxer", "Gixxer SF", "V Strom 250", "Hayabusa", "GSX-S750", 
    "V Strom 800DE", "V Strom DL650"
    ],
    "HERO": ["Xpulse 210", "Mavrick 440", "Xpulse 200", "Impulse"],
    "TRIUMPH": [
    "Tiger 900", "Tracker 400", "Scrambler 400 x", "Speed 400", 
    "Tiger Sport 660", "Tiger", "Trident 660"
    ],
    "TVS": [
    "Apache RTX 300 new", "tvs ronin", "Apache 200", "Apache RTR 160", "Apache RTR 310"
    ],
    "HARLEY DAVIDSON": ["Harley 440X"]
}

image_dir = r"e:\coad\hrx website 2\images"

all_images = []
for root, dirs, files in os.walk(image_dir):
    for f in files:
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            # Store relative path to use in HTML
            rel_path = os.path.relpath(os.path.join(root, f), image_dir).replace('\\', '/')
            all_images.append((f.lower(), "images/" + rel_path))

def normalize(name):
    name = name.lower()
    name = name.replace(" ", "")
    name = name.replace("_", "")
    name = name.replace("-", "")
    return name

mapping = {}

# Brand logos
for brand in brands_models.keys():
    brand_norm = normalize(brand)
    # Give priority to filenames containing the exact brand norm
    matches = [p for f, p in all_images if brand_norm in f and ('logo' in f or 'brand' in f)]
    if not matches:
        matches = [p for f, p in all_images if brand_norm in f]
    
    if matches:
        mapping[brand] = matches[0]
    else:
        # Default placeholder if not found
        mapping[brand] = "images/HRZ_BIKE_LOGO_page-0001-removebg-preview (3)_20250705_182254_0000.webp"

# Models
for brand, models in brands_models.items():
    for model in models:
        model_norm = normalize(model)
        # Search for exact substrings ignoring spaces/dashes
        matches = [p for f, p in all_images if model_norm in normalize(f)]
        if not matches:
            # Try fuzzy matching if exact substring fails
            all_basenames = [normalize(os.path.splitext(f)[0]) for f, p in all_images]
            close = difflib.get_close_matches(model_norm, all_basenames, n=1, cutoff=0.5)
            if close:
                # Find the corresponding path
                for f, p in all_images:
                    if normalize(os.path.splitext(f)[0]) == close[0]:
                        matches = [p]
                        break
        
        if matches:
            # Try to prefer FRONT views if available
            fronts = [m for m in matches if 'front' in m.lower()]
            mapping[model] = fronts[0] if fronts else matches[0]
        else:
            mapping[model] = "images/bike_t_1.webp"

with open(r'e:\coad\hrx website 2\js\image_map.js', 'w', encoding='utf-8') as f:
    f.write("window.HRzImageMap = " + json.dumps(mapping, indent=2) + ";\n")

print("Generated js/image_map.js")
