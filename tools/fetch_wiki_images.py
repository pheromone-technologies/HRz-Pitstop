import os
import json
import time
import requests

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

def search_wikimedia(query):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "generator": "search",
        "gsrsearch": query,
        "gsrlimit": 3,
        "pithumbsize": 500
    }
    try:
        resp = requests.get(url, params=params, headers={"User-Agent": "HRZ-Website-Builder/1.0"}, timeout=5).json()
        pages = resp.get("query", {}).get("pages", {})
        for pid, page in pages.items():
            if "thumbnail" in page:
                return page["thumbnail"]["source"]
    except Exception as e:
        print(f"Error fetching {query}: {e}")
    return None

mapping = {}

def fetch_image(query, filename):
    filepath = os.path.join(bikes_dir, filename)
    if os.path.exists(filepath):
        print(f"Skipping {query}, already exists.")
        return f"images/bikes/{filename}"
        
    print(f"Fetching {query}...")
    url = search_wikimedia(query)
    if not url:
        # Fallback to Wikimedia Commons directly
        url_commons = "https://commons.wikimedia.org/w/api.php"
        params_commons = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "generator": "search",
            "gsrsearch": "filetype:bitmap " + query,
            "gsrnamespace": 6,
            "gsrlimit": 1,
            "iiprop": "url",
            "iiurlwidth": 500
        }
        try:
            resp = requests.get(url_commons, params=params_commons, headers={"User-Agent": "HRZ/1.0"}).json()
            pages = resp.get("query", {}).get("pages", {})
            for pid, page in pages.items():
                info = page.get("imageinfo", [{}])[0]
                url = info.get("thumburl") or info.get("url")
                if url: break
        except Exception:
            pass

    if url:
        try:
            resp = requests.get(url, timeout=5, headers={"User-Agent": "HRZ/1.0"})
            if resp.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
                print(f"  -> Saved {filename}")
                return f"images/bikes/{filename}"
        except Exception as e:
            print(f"  -> Failed download: {e}")
            
    print(f"  -> Failed to find image for {query}")
    return None

print("Starting downloads...")

for brand, models in brands_models.items():
    brand_file = normalize(brand + "_logo")
    path = fetch_image(brand + " logo", brand_file)
    if path: mapping[brand] = path
    
    for model in models:
        model_file = normalize(brand + "_" + model)
        path = fetch_image(brand + " " + model + " motorcycle", model_file)
        if path: mapping[model] = path

# Fill missing with placeholders
for brand, models in brands_models.items():
    if brand not in mapping:
        mapping[brand] = 'images/HRZ_BIKE_LOGO_page-0001-removebg-preview (3)_20250705_182254_0000.webp'
    for model in models:
        if model not in mapping:
            # We don't want a generic placeholder that the user hates, but if wikipedia fails, we fallback
            mapping[model] = f"https://placehold.co/400x300/e0e0e0/555555?text={model.replace(' ', '+')}"

with open(r'e:\coad\hrx website 2\js\image_map.js', 'w', encoding='utf-8') as f:
    f.write("window.HRzImageMap = " + json.dumps(mapping, indent=2) + ";\n")

print("Done!")
