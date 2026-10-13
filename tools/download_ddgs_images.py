import os
import json
import time
import requests
from ddgs import DDGS

brands_models = {
    "ROYAL ENFIELD": ["Scram 440 new", "Classic 650", "Bear 650", "Guerrilla 450", "Himalayan 450", "SUPER METEOR 650", "Hunter 350", "Himalayan", "Classic 350 Reborn", "Standard 350 Reborn", "Meteor 350", "Classic", "Standard", "Electra", "Interceptor", "Thunderbird", "Thunderbird X", "Continental GT", "Scram"],
    "YAMAHA": ["XSR 155", "RX 100", "Aerox 155", "MT 15", "R3", "R15 V1", "R15 V2", "R15 V3", "R15 V4", "R1"],
    "KTM": ["KTM 390 Enduro R", "Adventure 890", "ADVENTURE 390 2025 Model", "Adventure 390", "Duke 125", "Duke 200", "Duke 250 BS6", "Duke 250", "Duke 390", "RC 390"],
    "BAJAJ": ["NS400Z", "Pulsar 220", "Pulsar NS 200", "Pulsar RS 200", "Dominar 400", "Pulsar 150", "Pulsar 180"],
    "HONDA": ["XL750 Transalp", "NX500", "CB 200X", "Hness CB 350", "Hornet 160R", "CBR 250 R", "CB 300", "CB 350 RS", "CB 500X", "NX400", "CB650R", "CBR 650R", "CBR 1000RR"],
    "SUZUKI": ["Gixxer", "Gixxer SF", "V Strom 250", "Hayabusa", "GSX-S750", "V Strom 800DE", "V Strom DL650"],
    "HERO": ["Xpulse 210", "Mavrick 440", "Xpulse 200", "Impulse"],
    "TRIUMPH": ["Tiger 900", "Tracker 400", "Scrambler 400 x", "Speed 400", "Tiger Sport 660", "Tiger", "Trident 660"],
    "TVS": ["Apache RTX 300 new", "tvs ronin", "Apache 200", "Apache RTR 160", "Apache RTR 310"],
    "HARLEY DAVIDSON": ["Harley 440X"]
}

bikes_dir = r"e:\coad\hrx website 2\images\bikes"
os.makedirs(bikes_dir, exist_ok=True)

def normalize(name):
    return name.replace(" ", "_").replace("/", "_") + ".jpg"

mapping = {}

# Load existing mapping if available
map_file = r'e:\coad\hrx website 2\js\image_map.js'
if os.path.exists(map_file):
    try:
        with open(map_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "window.HRzImageMap =" in content:
                json_str = content.split("window.HRzImageMap =")[1].strip().rstrip(";")
                mapping = json.loads(json_str)
    except:
        pass

ddgs = DDGS()

def fetch_image(query, filename):
    filepath = os.path.join(bikes_dir, filename)
    if os.path.exists(filepath):
        return f"images/bikes/{filename}"
        
    print(f"Fetching {query}...")
    for retry in range(3):
        try:
            results = ddgs.images(query, max_results=3)
            for r in results:
                url = r.get('image')
                if not url: continue
                try:
                    resp = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                    if resp.status_code == 200:
                        with open(filepath, 'wb') as f:
                            f.write(resp.content)
                        time.sleep(1) # delay to avoid rate limits
                        return f"images/bikes/{filename}"
                except:
                    continue
            break
        except Exception as e:
            print(f"  -> DDGS retry {retry} for {query}: {e}")
            time.sleep(3)
    return None

def save_map():
    with open(map_file, 'w', encoding='utf-8') as f:
        f.write("window.HRzImageMap = " + json.dumps(mapping, indent=2) + ";\n")

print("Starting robust download...")

for brand, models in brands_models.items():
    if brand not in mapping or 'placehold' in mapping[brand]:
        brand_file = normalize(brand + "_logo")
        path = fetch_image(brand + " motorcycle logo transparent", brand_file)
        if path:
            mapping[brand] = path
            save_map()
        else:
            mapping[brand] = 'images/HRZ_BIKE_LOGO_page-0001-removebg-preview (3)_20250705_182254_0000.webp'
            save_map()
            
    for model in models:
        if model not in mapping or 'placehold' in mapping[model] or 'bike_t_' in mapping[model]:
            model_file = normalize(brand + "_" + model)
            path = fetch_image(brand + " " + model + " motorcycle side view white background", model_file)
            if path:
                mapping[model] = path
                save_map()
            else:
                mapping[model] = "images/bike_t_1.webp"
                save_map()

print("Done!")
