import json
import urllib.request
import urllib.parse
import re

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

def get_image_url(query):
    query = urllib.parse.quote(query + " motorcycle")
    url = f"https://html.duckduckgo.com/html/?q={query}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        # Find the first image url in duckduckgo results
        match = re.search(r'img class="yY28I".*?src="(.*?)"', html)
        if match:
            # DuckDuckGo image URLs usually start with //
            img_url = match.group(1)
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            return img_url
    except Exception as e:
        print(f"Error for {query}: {e}")
    return None

results = {}
for brand, models in brands_models.items():
    print(f"Fetching for {brand} logo...")
    logo = get_image_url(brand + " logo transparent")
    results[brand] = logo
    
    for model in models:
        print(f"Fetching for {model}...")
        img = get_image_url(brand + " " + model)
        results[model] = img

with open('data/model_images.json', 'w') as f:
    json.dump(results, f, indent=2)

print("Done!")
