import json
import os
import re
import csv
from collections import defaultdict
import uuid

STAGING_FILE = 'staging.json'
IMAGE_DATA_DIR = 'image data'
IMAGES_DIR = 'images'

ALLOWED_BRANDS = {
    "Helmets": ["Axor", "SMK", "KYT", "Steelbird", "Vega", "Studds", "Royal Enfield"],
    "Gloves": ["Raida", "Cramster", "Axor", "Royal Enfield", "100%", "Fox", "DSG", "Scala", "Lone Ranger"],
    "Jackets": ["DSG", "Lone Ranger", "Raida", "Axor", "Cramster", "Scala"],
    "Tank bags": ["Raida", "Cramster", "Wild Heart", "Axor", "Moto Torque"],
    "Crash guards": ["Legundary Customs", "Moto Torque", "Bizen", "Moto Care", "MTechnics"],
    "Lubricants/Oils": ["AMS", "Motul", "Motomax"]
}

# Regex to extract colors at the end of the name.
COLOR_REGEX = re.compile(r'[-(\s]*\b(Black|Red|Blue|Grey|Green|White|Pink|Brown|Yellow|Orange|Purple|Silver|Gold|Matte Black|Gloss Black|Glossy Black|GreyGreen|Electric Blue|Forest Green|Fluo|Neon|Anthracite|Camo|Desert|Khaki)\b[-)\s]*$', re.IGNORECASE)

def normalize_brand(brand):
    if not brand: return ""
    b = brand.strip()
    if b.lower() == "axor helmets": return "Axor"
    if b.lower() == "100percent": return "100%"
    return b

def load_raw_data():
    raw_data = []
    for f in os.listdir(IMAGE_DATA_DIR):
        if f.endswith('.json'):
            path = os.path.join(IMAGE_DATA_DIR, f)
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for item in data:
                    item['_source_file'] = f
                    raw_data.append(item)
    return raw_data

def find_local_image(source_url, folder_hint):
    if not source_url: return None
    # We will just see if a local file exists. Mapping might be needed.
    # The source_url could be a web url. The downloaded file might be in images/<folder>/<filename>
    filename = source_url.split('?')[0].split('/')[-1]
    name, ext = os.path.splitext(filename)
    
    # Check images directory
    for root, dirs, files in os.walk(IMAGES_DIR):
        for f in files:
            if f == filename or f.startswith(name + "_") or f.startswith(name):
                # match found
                return os.path.join(root, f)
    return None

def process_staging(category_filter):
    raw_data = load_raw_data()
    staging = []
    
    for item in raw_data:
        # We only process if the raw category matches the target category
        # However, some might be categorized differently. Let's rely on raw category.
        cat = item.get('category', '')
        title_lower = item.get('title', '').lower()
        
        inferred_cat = cat
        if category_filter == 'Tank bags':
            if cat == 'Luggage' or 'bag' in title_lower or 'luggage' in title_lower:
                inferred_cat = 'Tank bags'
        elif category_filter == 'Crash guards':
            if cat == 'Protection' or 'guard' in title_lower or 'crash' in title_lower or 'plate' in title_lower or 'slider' in title_lower:
                inferred_cat = 'Crash guards'
        elif category_filter == 'Lubricants/Oils':
            if cat == 'Maintenance' or 'motul' in item.get('brand', '').lower() or 'oil' in title_lower or 'lube' in title_lower:
                inferred_cat = 'Lubricants/Oils'
                
        if inferred_cat != category_filter:
            continue
            
        cat = inferred_cat
            
        brand = normalize_brand(item.get('brand', ''))
        title = item.get('title', 'Unknown')
        
        # Determine base name and variant
        match = COLOR_REGEX.search(title)
        if match:
            variant = match.group(1).strip()
            base_name = title[:match.start()].strip()
            if base_name.endswith('-'): base_name = base_name[:-1].strip()
        else:
            variant = "Standard"
            base_name = title

        # For Helmets, maybe extract model differently, but we'll use base_name as product_name, and model as base_name too
        product_name = title
        model = base_name
        
        sku = item.get('id', str(uuid.uuid4()))
        mrp = item.get('price', 0)
        
        images = item.get('images', [])
        source_url = images[0] if images else ""
        
        # Attempt to find local image
        folder_hint = item['_source_file'].replace('.json', '')
        image_path = find_local_image(source_url, folder_hint)
        
        row = {
            "brand": brand,
            "category": cat,
            "product_name": product_name,
            "model": model,
            "variant": variant,
            "sku": sku,
            "mrp": mrp,
            "image_path": image_path,
            "source_url": source_url,
            "status": "pending",
            "_raw_item": item
        }
        staging.append(row)
        
    return staging

def classify(staging, target_category):
    allowed_brands = [b.lower() for b in ALLOWED_BRANDS.get(target_category, [])]
    
    # Calculate median mrp for anomaly detection (per brand)
    brand_prices = defaultdict(list)
    for r in staging:
        try:
            p = float(str(r['mrp']).replace(',', ''))
            if p > 0:
                brand_prices[r['brand']].append(p)
        except:
            pass
            
    median_prices = {}
    for b, prices in brand_prices.items():
        if prices:
            median_prices[b] = sorted(prices)[len(prices)//2]
            
    seen = set()
            
    for row in staging:
        status = "clean"
        b_lower = row['brand'].lower()
        
        if not b_lower:
            status = "unknown_brand"
        elif not any(ab == b_lower for ab in allowed_brands):
            # check if brand is completely unknown or just category mismatch
            all_known = [b.lower() for sublist in ALLOWED_BRANDS.values() for b in sublist]
            if b_lower not in all_known:
                status = "unknown_brand"
            else:
                status = "category_mismatch"
                
        # missing data
        elif not row['brand'] or not row['category'] or not row['product_name'] or not row['mrp']:
            status = "missing_data"
            
        # price anomaly (missing, zero, or outlier > 3x or < 1/3x median)
        elif status == "clean":
            try:
                p = float(str(row['mrp']).replace(',', ''))
                med = median_prices.get(row['brand'], 0)
                if p <= 0 or (med > 0 and (p > med * 3 or p < med / 3)):
                    status = "price_anomaly"
            except:
                status = "price_anomaly"
                
        # duplicate
        if status == "clean":
            dup_key = (row['brand'], row['category'], row['product_name'], row['variant'])
            if dup_key in seen:
                status = "duplicate"
            else:
                seen.add(dup_key)
                
        # image checks
        if status == "clean":
            if not row['image_path'] or not os.path.exists(row['image_path']):
                status = "missing_image"
                
        row['status'] = status
        
    return staging

def report(staging):
    counts = defaultdict(int)
    samples = defaultdict(list)
    for row in staging:
        counts[row['status']] += 1
        if len(samples[row['status']]) < 3:
            samples[row['status']].append(row['product_name'] + " (" + row['brand'] + ")")
            
    print("=== STEP 7 REPORT ===")
    for status, count in counts.items():
        print(f"{status}: {count}")
        print("  Samples:", samples[status])
        print()

if __name__ == "__main__":
    import sys
    cat = "Helmets"
    if len(sys.argv) > 1:
        cat = sys.argv[1]
        
    staging = process_staging(cat)
    staging = classify(staging, cat)
    
    with open(STAGING_FILE, 'w', encoding='utf-8') as f:
        # Avoid saving _raw_item to json to save space
        clean_staging = [{k:v for k,v in r.items() if k != '_raw_item'} for r in staging]
        json.dump(clean_staging, f, indent=2)
        
    report(staging)
