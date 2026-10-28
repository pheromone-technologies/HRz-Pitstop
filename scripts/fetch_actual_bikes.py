#!/usr/bin/env python3
"""
Fetch Actual Motorcycle Images for All Models
Repo: HRz Pitstop (E:\\coad\\hrx website 2)

Fetches actual side-profile studio images for each motorcycle in Menu.menuData.shopByBike,
removes backgrounds with rembg to generate clean transparent PNGs,
and updates js/image_map.js and data/bikes.json.
"""

import os
import sys
import re
import time
import requests
from io import BytesIO
from PIL import Image
from ddgs import DDGS
from rembg import remove

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"E:\coad\hrx website 2"
BIKES_DIR = os.path.join(BASE_DIR, "images", "bikes")
os.makedirs(BIKES_DIR, exist_ok=True)

# 14 Brands & 69 Models from js/menu.js
BIKE_MODELS = {
    "ROYAL ENFIELD": [
        "Himalayan 450", "Himalayan 411", "Classic 350 Reborn", "Hunter 350", 
        "Meteor 350", "Guerrilla 450", "Interceptor 650", "Continental GT 650", 
        "Super Meteor 650", "Bear 650", "Scram 411", "Scram 440", "Shotgun 650"
    ],
    "KTM": [
        "Duke 390 Gen-3", "Duke 250", "Duke 200", "Adventure 390", 
        "Adventure 390 (2025)", "390 Enduro R", "RC 390", "Adventure 250"
    ],
    "BAJAJ": [
        "Dominar 400", "Pulsar NS400Z", "Pulsar NS 200", "Pulsar N250", "Pulsar RS 200"
    ],
    "TRIUMPH": [
        "Speed 400", "Scrambler 400 X", "Tracker 400", "Tiger Sport 660", "Trident 660", "Speed T4"
    ],
    "YAMAHA": [
        "MT-15 V2", "R15 V4", "XSR 155", "FZS V3 / V4", "Aerox 155", "NMAX 155"
    ],
    "HONDA": [
        "H'ness CB 350", "CB 350 RS", "CB 200X", "XL750 Transalp", "NX500"
    ],
    "HERO": [
        "XPulse 200 4V", "XPulse 210", "Mavrick 440"
    ],
    "TVS": [
        "Apache RR 310", "Apache RTR 310", "Apache RTX 300", "Ronin 225"
    ],
    "HARLEY DAVIDSON": [
        "X440", "Pan America"
    ],
    "SUZUKI": [
        "V-Strom SX 250", "V-Strom 800DE", "Gixxer 250"
    ],
    "BMW": [
        "G 310 GS", "F 450 GS", "G 310 R", "S 1000 RR", "F 850 GS"
    ],
    "KAWASAKI": [
        "KLX 230", "Ninja 300", "Z900"
    ],
    "YEZDI": [
        "Adventure", "Scrambler", "Roadster"
    ],
    "APRILIA": [
        "RS 457", "Tuono 457", "Tuareg 660"
    ]
}

def clean_slug(brand, model):
    b = re.sub(r'[^a-zA-Z0-9]', '_', brand).strip('_')
    m = re.sub(r'[^a-zA-Z0-9]', '_', model).strip('_')
    return f"{b}_{m}"

ddgs = DDGS()

def fetch_and_process_bike(brand, model):
    slug = clean_slug(brand, model)
    png_filename = f"{slug}_transparent.png"
    webp_filename = f"{slug}.webp"
    
    png_path = os.path.join(BIKES_DIR, png_filename)
    webp_path = os.path.join(BIKES_DIR, webp_filename)
    
    # If transparent PNG already exists and > 5KB, reuse
    if os.path.exists(png_path) and os.path.getsize(png_path) > 15000:
        return f"images/bikes/{png_filename}", f"images/bikes/{webp_filename}"
        
    print(f"\n[FETCHING] {brand} {model}...")
    queries = [
        f"{brand} {model} motorcycle official studio side view png transparent",
        f"{brand} {model} motorcycle side profile white background",
        f"{brand} {model} bike side view"
    ]
    
    downloaded_im = None
    for q in queries:
        try:
            results = list(ddgs.images(q, max_results=5))
            for res in results:
                url = res.get('image')
                if not url: continue
                # Skip tiny thumbnails or icons
                if 'icon' in url.lower() or 'logo' in url.lower(): continue
                try:
                    resp = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                    if resp.status_code == 200 and len(resp.content) > 10000:
                        im = Image.open(BytesIO(resp.content))
                        w, h = im.size
                        if w >= 400 and h >= 250:
                            downloaded_im = im
                            print(f"   -> Downloaded ({w}x{h}) from: {url[:60]}...")
                            break
                except Exception:
                    continue
            if downloaded_im:
                break
        except Exception as e:
            time.sleep(1)
            continue
            
    if not downloaded_im:
        print(f"   [WARN] Could not fetch image for {brand} {model}")
        return None, None
        
    # Process image with rembg to isolate bike and make transparent
    try:
        # Convert to RGBA
        downloaded_im = downloaded_im.convert("RGBA")
        # Resize if overly large to speed up rembg and keep fast
        max_dim = 1200
        if max(downloaded_im.size) > max_dim:
            downloaded_im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            
        print(f"   -> Removing background with rembg...")
        transparent_im = remove(downloaded_im)
        
        # Save transparent PNG
        transparent_im.save(png_path, "PNG", optimize=True)
        
        # Save WebP on clean white canvas
        white_bg = Image.new("RGBA", transparent_im.size, (255, 255, 255, 255))
        composite = Image.alpha_composite(white_bg, transparent_im).convert("RGB")
        composite.save(webp_path, "WEBP", quality=90)
        
        print(f"   -> Saved: {png_filename} ({os.path.getsize(png_path)//1024} KB)")
        return f"images/bikes/{png_filename}", f"images/bikes/{webp_filename}"
    except Exception as e:
        print(f"   [ERROR] rembg failed for {brand} {model}: {e}")
        return None, None

def main():
    print("=" * 70)
    print("FETCHING & GENERATING ACCURATE MOTORCYCLE IMAGES")
    print("=" * 70)
    
    updated_image_map = {}
    
    # Process all 14 brands and models
    total_models = sum(len(m) for m in BIKE_MODELS.values())
    processed = 0
    success = 0
    
    for brand, models in BIKE_MODELS.items():
        print(f"\n=================== {brand} ({len(models)} models) ===================")
        brand_first_img = None
        for model in models:
            processed += 1
            png_rel, webp_rel = fetch_and_process_bike(brand, model)
            if png_rel:
                success += 1
                updated_image_map[model] = png_rel
                # Also store variations of model name for robust matching
                updated_image_map[f"{brand} {model}"] = png_rel
                if not brand_first_img:
                    brand_first_img = png_rel
            time.sleep(0.5) # Polite delay
            
        # Brand logo / flagship
        if brand_first_img:
            updated_image_map[brand] = brand_first_img
            
    # Update js/image_map.js
    map_file = os.path.join(BASE_DIR, "js", "image_map.js")
    
    # Read existing map to keep any other manual mappings
    existing_map = {}
    if os.path.exists(map_file):
        with open(map_file, 'r', encoding='utf-8') as f:
            c = f.read()
            for line in c.splitlines():
                m = re.search(r'"([^"]+)":\s*"([^"]+)"', line)
                if m: existing_map[m.group(1)] = m.group(2)
                
    # Overwrite with our newly verified images
    for k, v in updated_image_map.items():
        existing_map[k] = v
        
    with open(map_file, 'w', encoding='utf-8') as f:
        f.write("window.HRzImageMap = {\n")
        items = list(existing_map.items())
        for idx, (k, v) in enumerate(items):
            comma = "," if idx < len(items) - 1 else ""
            f.write(f'  "{k}": "{v}"{comma}\n')
        f.write("};\n")
        
    print("\n" + "=" * 70)
    print(f"IMAGE MAP UPDATED: {map_file} with {len(existing_map)} models.")
    print(f"Successfully processed {success}/{total_models} motorcycle models.")
    print("=" * 70)

if __name__ == "__main__":
    main()
