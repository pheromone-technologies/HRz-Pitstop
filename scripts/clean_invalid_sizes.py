import json
import re

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

# Categories and subcategories that genuinely have sizes
WEARABLE_CATEGORIES = {
    'Riding Jackets & Apparel', 'Riding Gears', 'Gloves', 'Riding Pants', 'Boots & Footwear', 'Apparel'
}

HELMET_WEARABLE_SUBCATS = {
    'Full-Face Helmet', 'Open-Face Helmet', 'Modular Helmet', 'Full Face', 'Open Face', 'Modular'
}

NON_SIZED_KEYWORDS = [
    'bluetooth', 'intercom', 'visor', 'spoiler', 'pinlock', 'mount', 'charger',
    'lock', 'cable', 'cover', 'strap', 'battery', 'mic', 'speaker', 'clamp',
    'screw', 'padding', 'mechanism', 'plate', 'guard', 'lube', 'clean', 'cleaner',
    'shampoo', 'spray', 'chain', 'fluid', 'bag', 'backpack', 'bladder', 'carrier',
    'stand', 'stay', 'oil', 'filter', 'light', 'lamp', 'bulb', 'indicator',
    'horn', 'switch', 'mirror', 'exhaust', 'bend', 'saddle', 'case', 'box',
    'earphone', 'headset', 'device', 'insert', 'antifog', 'anti-fog', 'tricorn'
]

cleaned_count = 0
for p in products:
    name_l = (p.get('name') or '').lower()
    cat = p.get('category') or ''
    subcat = p.get('subcategory') or ''
    
    # Check if this product is non-sized
    is_non_sized = False
    
    # Check keyword match
    if any(k in name_l for k in NON_SIZED_KEYWORDS):
        is_non_sized = True
        
    # Check category/subcategory
    if cat in ['Helmets & Accessories', 'Helmets']:
        # Only actual helmets have sizes, not accessories/visors
        if subcat in ['Helmet Accessories', 'Helmet Visor', 'Visors & Spoilers', 'Rider Tech'] or is_non_sized:
            is_non_sized = True
    elif cat in ['Bike Protection', 'Handlebar & Accessories', 'Lighting', 'Cleaning & Care', 
                 'Oil Caps & Stands', 'Bike Essentials & Fairings', 'Performance Accessories',
                 'Guards & Mounts', 'Foot Rests & Controls', 'Braking Components', 
                 'Drive & Transmission', 'Engine Oils & Lubricants', 'Electronics', 'Luggage & Touring', 'Luggage & Storage']:
        is_non_sized = True
        
    if is_non_sized:
        had_sizes = False
        for k in ['availableSizes', 'allSizes', 'sizes']:
            if k in p:
                del p[k]
                had_sizes = True
        if had_sizes:
            cleaned_count += 1

print(f"Cleaned invalid sizes from {cleaned_count} non-wearable products in data/products.json!")

with open('data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

with open('test design site/data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)
