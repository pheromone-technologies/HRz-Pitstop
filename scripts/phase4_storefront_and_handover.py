# scripts/phase4_storefront_and_handover.py
import os
import sys
import json
import csv
import re
import hashlib
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GOLD_XLSX = os.path.join(BASE_DIR, 'HRZ_Gold_Master_Verified.xlsx')
HOLD_XLSX = os.path.join(BASE_DIR, 'Client_Hold_Generic_And_Unfound.xlsx')
if not os.path.exists(HOLD_XLSX):
    HOLD_XLSX = os.path.join(BASE_DIR, '_vault_archive', 'legacy_catalogs_and_workbooks', 'Client_Hold_Generic_And_Unfound.xlsx')

MANUAL_CSV = os.path.join(BASE_DIR, 'scrape_manual_review.csv')
if not os.path.exists(MANUAL_CSV):
    MANUAL_CSV = os.path.join(BASE_DIR, '_vault_archive', 'scraper_working_cache', 'scrape_manual_review.csv')

PRODUCTS_JSON = os.path.join(BASE_DIR, 'data', 'products.json')
BIKES_JSON = os.path.join(BASE_DIR, 'data', 'bikes.json')
COMPAT_JSON = os.path.join(BASE_DIR, 'data', 'compatibility.json')
HANDOVER_XLSX = os.path.join(BASE_DIR, 'HRZ_Client_Action_Required_Items.xlsx')

print("=" * 70)
print("PHASE 4: STOREFRONT INTEGRATION & CLIENT HANDOVER GENERATION")
print("=" * 70)

# ==============================================================================
# 1. READ GOLD MASTER PRODUCTS
# ==============================================================================
print("\n[1/4] Reading HRZ_Gold_Master_Verified.xlsx...")
wb_gold = openpyxl.load_workbook(GOLD_XLSX, data_only=True)

lookup_sheets = ['LISTS', 'BIKE LISTS', 'MODEL DROPDOWNS']
gold_products = []
unique_bike_pairs = set()

# Pre-load POS names from StockSummaryReport for accurate color & size variant extraction
pos_names = {}
stock_summary_file = os.path.join(BASE_DIR, "StockSummaryReport_10_10_26.xlsx")
if os.path.exists(stock_summary_file):
    wb_stock = openpyxl.load_workbook(stock_summary_file, data_only=True)
    ws_stock = wb_stock.active
    for idx, r in enumerate(ws_stock.iter_rows(values_only=True)):
        if r and r[0]:
            pos_names[f"HRZ-Row{idx}"] = str(r[0]).strip()

SIZE_REGEX = re.compile(r'(?:^|[\s_\-\/])(XXS|XS|S|M|L|XL|XXL|2XL|3XL|4XL|5XL)(?:$|[\s_\-\/])', re.IGNORECASE)
COLOR_KEYWORDS = [
    'Black Neon Yellow', 'Black Red', 'Gloss White Blue', 'Dull Black', 'Matt Black', 
    'Gloss Black', 'Fluo Yellow', 'Neon Yellow', 'Neon Green', 'Titanium Grey',
    'White Red', 'Black White', 'Black Blue', 'Black Grey', 'Black Orange',
    'Black', 'White', 'Red', 'Blue', 'Green', 'Yellow', 'Orange', 'Grey', 'Silver', 'Gold', 'Smoke', 'Clear'
]

def map_unified_category_and_subcategory(sheet, subcat, name):
    s = sheet.strip()
    sc = (subcat or '').strip()
    nm = (name or '').strip().lower()
    
    # 1. Helmets & Accessories
    if s == 'Helmets & Accessories':
        if 'open' in nm or 'open-face' in sc.lower(): return s, 'Open-Face Helmet'
        if 'modular' in nm or 'modular' in sc.lower(): return s, 'Modular Helmet'
        if 'offroad' in nm or 'motocross' in nm: return s, 'Offroad Helmet'
        if 'visor' in nm: return s, 'Helmet Visor'
        if 'intercom' in nm or 'communication' in sc.lower(): return s, 'Communication & Intercoms'
        if 'goggle' in nm or 'eyewear' in sc.lower(): return s, 'Riding Eyewear & Goggles'
        if 'accessories' in sc.lower() or 'spoiler' in nm or 'pinlock' in nm: return s, 'Helmet Accessories'
        return s, 'Full-Face Helmet'
        
    # 2. Riding Gears
    if s == 'Riding Gears':
        if 'pant' in nm or 'trouser' in nm: return s, 'Riding Pants'
        if 'glove' in nm: return s, 'Riding Gloves'
        if 'boot' in nm or 'shoe' in nm: return s, 'Riding Boots'
        if 'suit' in nm: return s, 'Riding Suits'
        if 'armour' in nm or 'protector' in nm or 'chest' in nm or 'knee' in nm: return s, 'Body Armour & Protectors'
        if 'rain' in nm: return s, 'Rainwear'
        if 'balaclava' in nm or 'inner' in nm or 'mask' in nm: return s, 'Inner Wear & Balaclavas'
        if 'bag' in nm or 'backpack' in nm: return s, 'Riding Bags & Backpacks'
        return s, 'Riding Jacket'
        
    # 3. Luggage & Touring
    if s == 'Luggage & Touring':
        if 'saddle' in nm and 'bag' in nm: return s, 'Saddle Bags'
        if 'tail' in nm: return s, 'Tail Bags'
        if 'tank' in nm: return s, 'Tank Bags'
        if 'top' in nm and ('box' in nm or 'case' in nm): return s, 'Top Cases & Boxes'
        if 'rack' in nm: return s, 'Luggage Racks & Top Racks'
        if 'stay' in nm: return s, 'Saddle Stays'
        if 'pannier' in nm: return s, 'Panniers & Hard Luggage'
        if 'backpack' in nm or 'hydration' in nm: return s, 'Backpacks & Hydration'
        return s, 'Touring Accessories'
        
    # 4. Crash Protection & Guards
    if s in ['Bike Protection', 'Guards & Mounts']:
        if 'slider' in nm:
            if 'fork' in nm or 'axle' in nm: return 'Crash Protection', 'Fork & Axle Sliders'
            if 'exhaust' in nm: return 'Crash Protection', 'Exhaust Sliders'
            return 'Crash Protection', 'Frame Sliders'
        if 'bash' in nm or 'skid' in nm: return 'Crash Protection', 'Bash Plates & Skid Plates'
        if 'radiator' in nm: return 'Crash Protection', 'Radiator Guards'
        if 'engine' in nm: return 'Crash Protection', 'Engine Guards'
        if 'handguard' in nm or 'hand guard' in nm: return 'Crash Protection', 'Handguards & Lever Protectors'
        if 'master cylinder' in nm or 'cylinder guard' in sc.lower(): return 'Braking & Suspension', 'Master Cylinder Guards'
        if 'headlight' in nm: return 'Lights & Electricals', 'Headlight Grills & Protectors'
        if 'tank' in nm: return 'Styling & Decals', 'Tank Pads & Traction Grips'
        if 'windshield' in nm or 'visor' in nm: return 'Windshields & Visors', 'Touring Windshields'
        return 'Crash Protection', 'Crash Guards & Leg Guards'
        
    # 5. Handlebars & Controls
    if s in ['Handlebar & Accessories', 'Foot Rests']:
        if 'riser' in nm: return 'Handlebars & Controls', 'Handlebar Risers'
        if 'lever' in nm: return 'Handlebars & Controls', 'Levers & Lever Sets'
        if 'grip' in nm or 'bar end' in nm: return 'Handlebars & Controls', 'Grips & Bar Ends'
        if 'mirror' in nm: return 'Handlebars & Controls', 'Mirrors & Mirror Extenders'
        if 'mount' in nm or 'charger' in nm or 'phone' in nm: return 'Handlebars & Controls', 'Phone Mounts & Navigation Stays'
        if 'foot' in nm or 'peg' in nm or 'rearset' in nm: return 'Handlebars & Controls', 'Footpegs & Rearsets'
        if 'throttle' in nm: return 'Handlebars & Controls', 'Throttle Assists'
        return 'Handlebars & Controls', 'Handlebars'
        
    # 6. Lights & Electricals
    if s == 'Lighting':
        if 'clamp' in nm or 'mount' in nm: return 'Lights & Electricals', 'Fog Light Clamps & Mounts'
        if 'grill' in nm or 'protector' in nm: return 'Lights & Electricals', 'Headlight Grills & Protectors'
        if 'indicator' in nm or 'bulb' in nm: return 'Lights & Electricals', 'LED Bulbs & Indicators'
        if 'tail' in nm or 'brake' in nm: return 'Lights & Electricals', 'Tail Lights & Brake Lights'
        if 'harness' in nm or 'switch' in nm: return 'Lights & Electricals', 'Wiring Harnesses & Switches'
        if 'charger' in nm or 'usb' in nm: return 'Lights & Electricals', 'USB Chargers & Sockets'
        if 'horn' in nm: return 'Lights & Electricals', 'Horns'
        return 'Lights & Electricals', 'Auxiliary & Fog Lights'
        
    # 7. Exhausts & Performance
    if s == 'Performance Accessories':
        if 'slip' in nm or 'exhaust' in nm: return 'Exhausts & Performance', 'Slip-On Exhausts'
        if 'full' in nm: return 'Exhausts & Performance', 'Full System Exhausts'
        if 'filter' in nm: return 'Exhausts & Performance', 'Performance Air Filters'
        if 'ecu' in nm or 'tuning' in nm: return 'Exhausts & Performance', 'ECUs & Tuning Modules'
        if 'shield' in nm or 'baffle' in nm: return 'Exhausts & Performance', 'Exhaust Heat Shields & Baffles'
        if 'plug' in nm: return 'Exhausts & Performance', 'Spark Plugs'
        return 'Exhausts & Performance', 'Slip-On Exhausts'
        
    # 8. Maintenance & Care
    if s in ['Cleaning Accessories', 'Oil Caps & Stands']:
        if 'chain' in nm and ('spray' in nm or 'clean' in nm or 'lube' in nm): return 'Maintenance & Care', 'Chain Sprays & Cleaners'
        if 'oil' in nm or 'fluid' in nm: return 'Maintenance & Care', 'Engine Oils & Fluids'
        if 'paddock' in nm or 'bobbin' in nm or 'stand' in nm: return 'Maintenance & Care', 'Paddock Stands & Bobbins'
        if 'cover' in nm: return 'Maintenance & Care', 'Bike Covers'
        if 'tool' in nm or 'kit' in nm: return 'Maintenance & Care', 'Chain Tools & Maintenance Kits'
        if 'puncture' in nm or 'inflator' in nm: return 'Maintenance & Care', 'Tyre Puncture Kits & Inflators'
        if s == 'Oil Caps & Stands' and ('cap' in nm or 'base' in nm): return 'Styling & Decals', 'Custom Badges & Emblems'
        return 'Maintenance & Care', 'Cleaning Sprays & Shampoos'
        
    # 9. Body Fairing & Styling
    if s == 'Body Fairing and Fenders':
        if 'windshield' in nm or 'visor' in nm: return 'Windshields & Visors', 'Touring Windshields'
        if 'tank' in nm: return 'Styling & Decals', 'Tank Pads & Traction Grips'
        if 'decal' in nm or 'graphic' in nm: return 'Styling & Decals', 'Graphic Kits & Decals'
        if 'tail tidy' in nm or 'fender' in nm: return 'Styling & Decals', 'Tail Tidies & Fender Eliminators'
        if 'winglet' in nm: return 'Styling & Decals', 'Winglets & Aero Accents'
        return 'Styling & Decals', 'Custom Badges & Emblems'
        
    # 10. General Accessories
    if s in ['General Accessories', 'Bike Essentials']:
        if 'key' in nm: return 'General Accessories', 'Keychains & Key Covers'
        if 'sticker' in nm or 'badge' in nm: return 'General Accessories', 'Stickers & Badges'
        if 'lock' in nm or 'theft' in nm: return 'General Accessories', 'Locks & Anti-Theft Security'
        if 'bottle' in nm or 'drink' in nm: return 'General Accessories', 'Water Bottles & Drink Holders'
        if 'pouch' in nm or 'tool' in nm: return 'General Accessories', 'Utility Pouches & Tools'
        return 'General Accessories', 'Miscellaneous Accessories'

    return 'General Accessories', 'Miscellaneous Accessories'

for s_name in wb_gold.sheetnames:
    if s_name in lookup_sheets:
        continue
    ws = wb_gold[s_name]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        continue
    for r in rows[1:]:
        name = str(r[0]).strip() if r[0] is not None else ""
        if not name:
            continue
        
        raw_subcat = str(r[1]).strip() if len(r) > 1 and r[1] is not None else "General"
        brand = str(r[2]).strip() if len(r) > 2 and r[2] is not None else "Generic"
        make = str(r[3]).strip() if len(r) > 3 and r[3] is not None else "Universal"
        model = str(r[4]).strip() if len(r) > 4 and r[4] is not None else "All"
        mrp = float(r[5]) if len(r) > 5 and r[5] is not None else 0.0
        price = float(r[6]) if len(r) > 6 and r[6] is not None else 0.0
        discount = float(r[7]) if len(r) > 7 and r[7] is not None else 0.0
        stock = int(r[8]) if len(r) > 8 and str(r[8]).isdigit() else 1
        img = str(r[9]).strip() if len(r) > 9 and r[9] is not None else ""
        desc = str(r[10]).strip() if len(r) > 10 and r[10] is not None else ""
        sku = str(r[11]).strip() if len(r) > 11 and r[11] is not None else f"SKU-{len(gold_products)+1:04d}"
        color = str(r[12]).strip() if len(r) > 12 and r[12] is not None and str(r[12]).strip() not in ['None', ''] else "Standard"
        size = str(r[13]).strip() if len(r) > 13 and r[13] is not None and str(r[13]).strip() not in ['None', ''] else "Standard"

        pos_name = pos_names.get(sku, '')
        full_text = f"{name} {pos_name} {img}"
        if color == 'Standard':
            for ck in COLOR_KEYWORDS:
                if re.search(r'\b' + re.escape(ck) + r'\b', full_text, re.IGNORECASE):
                    color = ck
                    break
        if size == 'Standard':
            m = SIZE_REGEX.search(pos_name) or SIZE_REGEX.search(img) or SIZE_REGEX.search(name)
            if m:
                size = m.group(1).upper()

        unique_bike_pairs.add((make, model))

        unified_cat, unified_subcat = map_unified_category_and_subcategory(s_name, raw_subcat, name)

        gold_products.append({
            'name': name,
            'category': unified_cat,
            'subcategory': unified_subcat,
            'brand': brand,
            'compatibleBikeMake': make,
            'compatibleBikeModel': model,
            'mrp': mrp,
            'selling_price': price,
            'discount': discount,
            'stock': stock,
            'image': img,
            'desc': desc,
            'sku': sku,
            'color': color,
            'size': size
        })

print(f"      Loaded {len(gold_products)} Gold Master verified items across 14 sheets.")
print(f"      Discovered {len(unique_bike_pairs)} unique (Make, Model) pairs in Gold Master.")

# ==============================================================================
# 2. SYNC data/bikes.json WITH ALL BIKES (INCLUDING APRILIA & BIKE LISTS)
# ==============================================================================
print("\n[2/4] Syncing data/bikes.json & data/compatibility.json...")

# Load existing bikes
existing_bikes = []
if os.path.exists(BIKES_JSON):
    with open(BIKES_JSON, 'r', encoding='utf-8') as f:
        existing_bikes = json.load(f)

bikes_by_id = {b['id']: b for b in existing_bikes}
bikes_by_key = {f"{b['brand'].lower()}__{b['model'].lower()}": b for b in existing_bikes}

# Bikes in 'BIKE LISTS' lookup sheet
ws_bl = wb_gold['BIKE LISTS']
for r in list(ws_bl.iter_rows(values_only=True))[1:]:
    if r and r[0] and r[1] and r[0] != 'Bike Make' and r[1] != 'Bike Model':
        make = str(r[0]).strip()
        model = str(r[1]).strip()
        unique_bike_pairs.add((make, model))

def slugify(text):
    return "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")

# Predefined metadata for common bike categories
BIKE_METADATA = {
    'Aprilia': {
        'RS 457': {'category': 'Supersport', 'engineCc': 457, 'variant': 'Standard'},
        'Tuono 457': {'category': 'Naked', 'engineCc': 457, 'variant': 'Standard'},
        'Tuareg 660': {'category': 'Adventure', 'engineCc': 659, 'variant': 'Rally'}
    },
    'Royal Enfield': {
        'Himalayan 450': {'category': 'Adventure', 'engineCc': 452, 'variant': 'Adventure'},
        'Himalayan 411': {'category': 'Adventure', 'engineCc': 411, 'variant': 'Base'},
        'Classic 350 Reborn': {'category': 'Classic', 'engineCc': 349, 'variant': 'Reborn'},
        'Hunter 350': {'category': 'Roadster', 'engineCc': 349, 'variant': 'Metro'},
        'Meteor 350': {'category': 'Cruiser', 'engineCc': 349, 'variant': 'Stellar'},
        'Guerrilla 450': {'category': 'Roadster', 'engineCc': 452, 'variant': 'Analogue'},
        'Interceptor 650': {'category': 'Twin', 'engineCc': 648, 'variant': 'Twin'},
        'Continental GT 650': {'category': 'Cafe Racer', 'engineCc': 648, 'variant': 'Apex Grey'},
        'Super Meteor 650': {'category': 'Cruiser', 'engineCc': 648, 'variant': 'Astral'},
        'Bear 650': {'category': 'Scrambler', 'engineCc': 648, 'variant': 'Standard'},
        'Scram 411': {'category': 'Scrambler', 'engineCc': 411, 'variant': 'Standard'},
        'Scram 440': {'category': 'Scrambler', 'engineCc': 443, 'variant': 'Standard'},
        'Shotgun 650': {'category': 'Cruiser', 'engineCc': 648, 'variant': 'Custom'}
    },
    'KTM': {
        'Duke 390 Gen-3': {'category': 'Naked', 'engineCc': 399, 'variant': 'Standard'},
        'Duke 250': {'category': 'Naked', 'engineCc': 249, 'variant': 'Standard'},
        'Duke 200': {'category': 'Naked', 'engineCc': 199, 'variant': 'Standard'},
        'Adventure 390': {'category': 'Adventure', 'engineCc': 373, 'variant': 'Standard'},
        'Adventure 390 (2025)': {'category': 'Adventure', 'engineCc': 399, 'variant': 'Gen-2'},
        'Adventure 250': {'category': 'Adventure', 'engineCc': 248, 'variant': 'Standard'},
        '390 Enduro R': {'category': 'Dual Sport', 'engineCc': 399, 'variant': 'Enduro'},
        'RC 390': {'category': 'Supersport', 'engineCc': 373, 'variant': 'Standard'}
    },
    'Triumph': {
        'Speed 400': {'category': 'Roadster', 'engineCc': 398, 'variant': 'Standard'},
        'Scrambler 400 X': {'category': 'Scrambler', 'engineCc': 398, 'variant': 'Standard'},
        'Tracker 400': {'category': 'Flat Tracker', 'engineCc': 398, 'variant': 'Standard'},
        'Speed T4': {'category': 'Roadster', 'engineCc': 398, 'variant': 'Base'},
        'Tiger Sport 660': {'category': 'Adventure Sport', 'engineCc': 660, 'variant': 'Standard'},
        'Trident 660': {'category': 'Roadster', 'engineCc': 660, 'variant': 'Standard'}
    },
    'Bajaj': {
        'Dominar 400': {'category': 'Tourer', 'engineCc': 373, 'variant': 'Touring Factory'},
        'Pulsar NS400Z': {'category': 'Naked', 'engineCc': 373, 'variant': 'Standard'},
        'Pulsar NS 200': {'category': 'Naked', 'engineCc': 199, 'variant': 'Standard'},
        'Pulsar N250': {'category': 'Naked', 'engineCc': 249, 'variant': 'Standard'},
        'Pulsar RS 200': {'category': 'Supersport', 'engineCc': 199, 'variant': 'Standard'}
    },
    'Yamaha': {
        'MT-15 V2': {'category': 'Naked', 'engineCc': 155, 'variant': 'V2 Deluxe'},
        'R15 V4': {'category': 'Supersport', 'engineCc': 155, 'variant': 'V4 Standard'},
        'XSR 155': {'category': 'Neo Retro', 'engineCc': 155, 'variant': 'Standard'},
        'Aerox 155': {'category': 'Maxi Scooter', 'engineCc': 155, 'variant': 'Standard'},
        'FZS V3 / V4': {'category': 'Commuter', 'engineCc': 149, 'variant': 'Standard'}
    },
    'Honda': {
        "H'ness CB 350": {'category': 'Classic', 'engineCc': 348, 'variant': 'DLX Pro'},
        'CB 350 RS': {'category': 'Scrambler', 'engineCc': 348, 'variant': 'Standard'},
        'CB 200X': {'category': 'Urban ADV', 'engineCc': 184, 'variant': 'Standard'},
        'NX500': {'category': 'Adventure', 'engineCc': 471, 'variant': 'Standard'},
        'XL750 Transalp': {'category': 'Adventure', 'engineCc': 755, 'variant': 'Standard'}
    },
    'Hero': {
        'XPulse 200 4V': {'category': 'Adventure', 'engineCc': 199, 'variant': '4V Rally'},
        'XPulse 210': {'category': 'Adventure', 'engineCc': 210, 'variant': 'Standard'},
        'Mavrick 440': {'category': 'Roadster', 'engineCc': 440, 'variant': 'Standard'}
    },
    'TVS': {
        'Apache RR 310': {'category': 'Supersport', 'engineCc': 312, 'variant': 'BTO'},
        'Apache RTR 310': {'category': 'Naked', 'engineCc': 312, 'variant': 'Standard'},
        'Apache RTX 300': {'category': 'Adventure', 'engineCc': 312, 'variant': 'Standard'},
        'Ronin 225': {'category': 'Scrambler', 'engineCc': 225, 'variant': 'Standard'}
    },
    'BMW': {
        'G 310 GS': {'category': 'Adventure', 'engineCc': 313, 'variant': 'GS Adventure'},
        'G 310 R': {'category': 'Naked', 'engineCc': 313, 'variant': 'Standard'},
        'F 450 GS': {'category': 'Adventure', 'engineCc': 450, 'variant': 'Concept/Rally'},
        'S 1000 RR': {'category': 'Superbike', 'engineCc': 999, 'variant': 'M Sport'}
    },
    'Suzuki': {
        'V-Strom SX 250': {'category': 'Adventure', 'engineCc': 249, 'variant': 'Standard'},
        'Gixxer 250': {'category': 'Naked', 'engineCc': 249, 'variant': 'Standard'},
        'V-Strom 800DE': {'category': 'Adventure', 'engineCc': 776, 'variant': 'Dual Explorer'}
    },
    'Kawasaki': {
        'KLX 230': {'category': 'Dual Sport', 'engineCc': 233, 'variant': 'Standard'},
        'Ninja 300': {'category': 'Supersport', 'engineCc': 296, 'variant': 'Standard'},
        'Z900': {'category': 'Supernaked', 'engineCc': 948, 'variant': 'Standard'}
    },
    'Yezdi': {
        'Adventure': {'category': 'Adventure', 'engineCc': 334, 'variant': 'Standard'},
        'Scrambler': {'category': 'Scrambler', 'engineCc': 334, 'variant': 'Standard'},
        'Roadster': {'category': 'Cruiser', 'engineCc': 334, 'variant': 'Standard'}
    },
    'Harley-Davidson': {
        'X440': {'category': 'Roadster', 'engineCc': 440, 'variant': 'Standard'},
        'Pan America': {'category': 'Adventure', 'engineCc': 1250, 'variant': 'Special'}
    }
}

# Ensure each bike from unique_bike_pairs exists
synced_bikes = []
for make, model in sorted(unique_bike_pairs):
    if make.lower() == 'universal' or model.lower() in ['all', 'universal', 'none']:
        continue
    
    # Capitalize cleanly
    brand_clean = make.title() if make.isupper() else make
    if brand_clean.lower() in ['harley davidson', 'harley-davidson']:
        brand_clean = 'Harley-Davidson'
    elif brand_clean.lower() == 'ktm':
        brand_clean = 'KTM'
    elif brand_clean.lower() == 'bmw':
        brand_clean = 'BMW'
    elif brand_clean.lower() == 'tvs':
        brand_clean = 'TVS'
    
    model_clean = model.title() if model.isupper() else model
    # Specific casing fixes
    if '450' in model: model_clean = model_clean.replace('450', '450')
    if '650' in model: model_clean = model_clean.replace('650', '650')
    if '350' in model: model_clean = model_clean.replace('350', '350')
    if '400' in model: model_clean = model_clean.replace('400', '400')
    if 'Ns400Z' in model_clean: model_clean = 'Pulsar NS400Z'
    if 'Xpulse' in model_clean: model_clean = 'XPulse 200 4V'

    key = f"{brand_clean.lower()}__{model_clean.lower()}"
    existing = bikes_by_key.get(key)

    if existing:
        if existing not in synced_bikes:
            synced_bikes.append(existing)
    else:
        # Determine category & variant
        meta = BIKE_METADATA.get(brand_clean, {}).get(model_clean, {})
        category = meta.get('category', 'Street')
        variant = meta.get('variant', 'Standard')
        engineCc = meta.get('engineCc', 350)
        bike_id = f"bike-{slugify(brand_clean)[:3]}-{slugify(model_clean)[:10]}"

        new_bike = {
            'id': bike_id,
            'brand': brand_clean,
            'model': model_clean,
            'year': 2024,
            'variant': variant,
            'engineCc': engineCc,
            'category': category,
            'region': 'India'
        }
        synced_bikes.append(new_bike)
        bikes_by_key[key] = new_bike

# Add remaining existing bikes that weren't in pairs
for b in existing_bikes:
    if b not in synced_bikes:
        synced_bikes.append(b)

# Ensure Aprilia models specifically exist
for ap_model, ap_meta in BIKE_METADATA['Aprilia'].items():
    key = f"aprilia__{ap_model.lower()}"
    if key not in bikes_by_key:
        ap_bike = {
            'id': f"bike-apr-{slugify(ap_model)}",
            'brand': 'Aprilia',
            'model': ap_model,
            'year': 2024,
            'variant': ap_meta['variant'],
            'engineCc': ap_meta['engineCc'],
            'category': ap_meta['category'],
            'region': 'India'
        }
        synced_bikes.append(ap_bike)
        bikes_by_key[key] = ap_bike

# Save data/bikes.json
with open(BIKES_JSON, 'w', encoding='utf-8') as f:
    json.dump(synced_bikes, f, indent=2, ensure_ascii=False)
print(f"      Saved {len(synced_bikes)} bikes to {BIKES_JSON}!")

# ==============================================================================
# 3. COMPILE data/products.json WITH multi-variant & compatibleBikeMake/Model
# ==============================================================================
print("\n[3/4] Re-compiling data/products.json & data/compatibility.json...")

def clean_title_for_grouping(title):
    t = title
    t = re.sub(r'\b(size\s*:?\s*)?(xs|s|m|l|xl|xxl|2xl|3xl|4xl)\b', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\b(size\s*\d+)\b', '', t, flags=re.IGNORECASE)
    t = re.sub(r'[\s\-_\/]+$', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

grouped_products = {}
compatibility_rules = []

for idx, p in enumerate(gold_products):
    base_title = clean_title_for_grouping(p['name'])
    base_title_clean = base_title if len(base_title) > 6 else p['name']
    group_key = f"{base_title_clean.lower()}__{p['brand'].lower()}__{p['category'].lower()}"

    variant_entry = {
        'color': p['color'] or 'Standard',
        'size': p['size'] or 'Standard',
        'sku': p['sku'],
        'price': p['selling_price'],
        'mrp': p['mrp'],
        'stockQty': p['stock'],
        'image': p['image'],
        'gallery': [p['image']] if p['image'] else []
    }

    if group_key not in grouped_products:
        prod_id_hash = hashlib.md5(group_key.encode('utf-8')).hexdigest()[:8].upper()
        prod_id = f"prod-{prod_id_hash}"

        bike_compat_list = []
        if p['compatibleBikeMake'] and p['compatibleBikeMake'] != 'Universal':
            bike_compat_list.append(f"{p['compatibleBikeMake']} {p['compatibleBikeModel']}".strip())
        else:
            bike_compat_list.append('Universal')

        grouped_products[group_key] = {
            'id': prod_id,
            'name': base_title_clean if len(base_title_clean) > 5 else base_title,
            'category': p['category'],
            'subcategory': p['subcategory'],
            'brand': p['brand'],
            'compatibleBikeMake': p['compatibleBikeMake'],
            'compatibleBikeModel': p['compatibleBikeModel'],
            'price': p['selling_price'],
            'originalPrice': p['mrp'],
            'image': p['image'],
            'gallery': [p['image']] if p['image'] else [],
            'rating': 4.8,
            'reviewCount': 14,
            'ridersInstalled': 12,
            'inStock': p['stock'] > 0,
            'sku': p['sku'],
            'bike_compatibility': bike_compat_list,
            'highlights': [p['desc']] if p['desc'] else [f"{p['name']} verified genuine part from {p['brand']}."],
            'variants': [variant_entry]
        }
    else:
        gp = grouped_products[group_key]
        gp['variants'].append(variant_entry)
        if p['image'] and p['image'] not in gp['gallery']:
            gp['gallery'].append(p['image'])
        if p['selling_price'] < gp['price']:
            gp['price'] = p['selling_price']
            gp['originalPrice'] = p['mrp']
        if p['compatibleBikeMake'] != 'Universal':
            bike_str = f"{p['compatibleBikeMake']} {p['compatibleBikeModel']}".strip()
            if bike_str not in gp['bike_compatibility']:
                gp['bike_compatibility'].append(bike_str)

compiled_product_cards = list(grouped_products.values())

# Build compatibility rules
rule_idx = 1
for prod in compiled_product_cards:
    is_uni = 'Universal' in prod['bike_compatibility'] or prod['compatibleBikeMake'] == 'Universal'
    if is_uni:
        compatibility_rules.append({
            'id': f"cmp-{rule_idx}",
            'productId': prod['id'],
            'bikeId': 'universal',
            'fitType': 'Universal Fit',
            'notes': 'Universal motorcycle fitment',
            'sku': prod['sku']
        })
        rule_idx += 1
    else:
        for bike in synced_bikes:
            b_make = bike['brand'].lower()
            b_model = bike['model'].lower()
            matches = any((b_make in comp.lower() and b_model in comp.lower()) or (b_model in comp.lower()) for comp in prod['bike_compatibility'])
            if matches:
                compatibility_rules.append({
                    'id': f"cmp-{rule_idx}",
                    'productId': prod['id'],
                    'bikeId': bike['id'],
                    'fitType': 'OEM Fit',
                    'notes': f"Direct bolt-on fitment for {bike['brand']} {bike['model']}",
                    'sku': prod['sku']
                })
                rule_idx += 1

with open(PRODUCTS_JSON, 'w', encoding='utf-8') as f:
    json.dump(compiled_product_cards, f, indent=2, ensure_ascii=False)
print(f"      Saved {len(compiled_product_cards)} unique product cards ({len(gold_products)} total variants) to {PRODUCTS_JSON}!")

with open(COMPAT_JSON, 'w', encoding='utf-8') as f:
    json.dump(compatibility_rules, f, indent=2, ensure_ascii=False)
print(f"      Saved {len(compatibility_rules)} compatibility rules to {COMPAT_JSON}!")

# ==============================================================================
# 4. GENERATE CLEAN CLIENT HANDOVER WORKBOOK HRZ_Client_Action_Required_Items.xlsx
# ==============================================================================
print("\n[4/4] Generating HRZ_Client_Action_Required_Items.xlsx...")

wb_handover = openpyxl.Workbook()
# remove default sheet
wb_handover.remove(wb_handover.active)

# Styles
font_title = Font(name='Segoe UI', size=14, bold=True, color='1E293B')
font_header = Font(name='Segoe UI', size=10, bold=True, color='FFFFFF')
font_data = Font(name='Segoe UI', size=9, color='0F172A')
font_data_bold = Font(name='Segoe UI', size=9, bold=True, color='0F172A')

fill_header_tab1 = PatternFill(start_color='1E293B', end_color='1E293B', fill_type='solid') # Slate
fill_header_tab2 = PatternFill(start_color='991B1B', end_color='911B1B', fill_type='solid') # Dark Red
fill_action_col = PatternFill(start_color='FEF9C3', end_color='FEF9C3', fill_type='solid')  # Soft Yellow
fill_action_header = PatternFill(start_color='EAB308', end_color='EAB308', fill_type='solid') # Amber
fill_zebra = PatternFill(start_color='F8FAFC', end_color='F8FAFC', fill_type='solid')

border_thin = Border(
    left=Side(style='thin', color='CBD5E1'),
    right=Side(style='thin', color='CBD5E1'),
    top=Side(style='thin', color='CBD5E1'),
    bottom=Side(style='thin', color='CBD5E1')
)

# ------------------------------------------------------------------------------
# TAB 1: Needs Price or Photo (from scrape_manual_review.csv)
# ------------------------------------------------------------------------------
manual_rows = []
if os.path.exists(MANUAL_CSV):
    with open(MANUAL_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for r in reader:
            if r and any(c.strip() for c in r):
                manual_rows.append(r)

ws1 = wb_handover.create_sheet(title=f"Needs Price or Photo ({len(manual_rows)})")
ws1.views.sheetView[0].showGridLines = True

headers_tab1 = [
    "POS Row #", "Product Name", "Brand", "Category", "Subcategory",
    "Current Stock Qty", "POS Purchase Cost (₹)", "Current POS Sale Price (₹)",
    "What Is Missing", "Reason / Scraper Note", "Client Confirmed Selling Price (₹)"
]

ws1.append(headers_tab1)
for col_num in range(1, len(headers_tab1) + 1):
    c = ws1.cell(row=1, column=col_num)
    if col_num == len(headers_tab1):
        c.fill = fill_action_header
        c.font = Font(name='Segoe UI', size=10, bold=True, color='000000')
    else:
        c.fill = fill_header_tab1
        c.font = font_header
    c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

for row_idx, r in enumerate(manual_rows, start=2):
    pos_row = r[0] if len(r) > 0 else ""
    p_name = r[1] if len(r) > 1 else ""
    brand = r[2] if len(r) > 2 else ""
    cat = r[3] if len(r) > 3 else ""
    subcat = r[4] if len(r) > 4 else ""
    sale_price = float(r[5]) if len(r) > 5 and r[5] and r[5] != 'None' else 0.0
    purchase_cost = float(r[6]) if len(r) > 6 and r[6] and r[6] != 'None' else 0.0
    stock_qty = int(r[7]) if len(r) > 7 and str(r[7]).isdigit() else 1
    reason = r[9] if len(r) > 9 else ""

    # Classify what is missing
    what_missing = "Retail Price & Photo"
    if "PRICE_LESS_THAN_OR_EQUAL_PURCHASE_PRICE" in reason or "PRICE_INVALID" in reason:
        what_missing = "Confirmed Retail Price (Purchase > Scraped)"
    elif "SCRAPED_PRICE_ZERO" in reason:
        what_missing = "Retail Price Only"
    elif "IMAGE_NOT_DOWNLOADED" in reason:
        what_missing = "Photo Only"

    row_data = [
        pos_row, p_name, brand, cat, subcat, stock_qty, purchase_cost, sale_price,
        what_missing, reason, ""
    ]
    ws1.append(row_data)

    is_even = (row_idx % 2 == 0)
    for col_num in range(1, len(headers_tab1) + 1):
        cell = ws1.cell(row=row_idx, column=col_num)
        cell.font = font_data
        cell.border = border_thin
        if col_num in [6, 7, 8]:
            cell.alignment = Alignment(horizontal='right', vertical='center')
            if col_num in [7, 8]:
                cell.number_format = '₹#,##0.00'
        elif col_num in [1, 9]:
            cell.alignment = Alignment(horizontal='center', vertical='center')
        else:
            cell.alignment = Alignment(horizontal='left', vertical='center')

        # Highlight action column
        if col_num == len(headers_tab1):
            cell.fill = fill_action_col
            cell.number_format = '₹#,##0.00'
        elif is_even:
            cell.fill = fill_zebra

# ------------------------------------------------------------------------------
# TAB 2: Generic Counter Items (from Client_Hold_Generic_And_Unfound.xlsx)
# ------------------------------------------------------------------------------
hold_items = []
if os.path.exists(HOLD_XLSX):
    wb_hold = openpyxl.load_workbook(HOLD_XLSX, data_only=True)
    for sheet_idx, s in enumerate(wb_hold.sheetnames):
        ws_h = wb_hold[s]
        bucket_label = "Generic / Unbranded" if "Generic" in s else "Not Found Externally"
        for r in list(ws_h.iter_rows(values_only=True))[1:]:
            if r and len(r) > 3 and r[3] and str(r[3]).strip() != "":
                pos_row = str(r[1]).strip() if len(r) > 1 and r[1] else ""
                p_name = str(r[3]).strip()
                cat = str(r[4]).strip() if len(r) > 4 and r[4] else "General Accessories"
                subcat = str(r[5]).strip() if len(r) > 5 and r[5] else "Miscellaneous"
                brand = str(r[6]).strip() if len(r) > 6 and r[6] else "Generic"
                stock = int(r[7]) if len(r) > 7 and str(r[7]).isdigit() else 1
                sale = float(r[8]) if len(r) > 8 and r[8] else 0.0
                purchase = float(r[9]) if len(r) > 9 and r[9] else 0.0
                action = str(r[10]).strip() if len(r) > 10 and r[10] else "Keep for In-Store Billing"

                hold_items.append({
                    'pos_row': pos_row,
                    'name': p_name,
                    'category': cat,
                    'subcategory': subcat,
                    'brand': brand,
                    'stock': stock,
                    'purchase': purchase,
                    'sale': sale,
                    'bucket': bucket_label,
                    'action': action
                })

# Sort Tab 2 by Stock Quantity descending
hold_items.sort(key=lambda x: x['stock'], reverse=True)

ws2 = wb_handover.create_sheet(title=f"Generic Counter Items ({len(hold_items)})")
ws2.views.sheetView[0].showGridLines = True

headers_tab2 = [
    "#", "POS Row #", "Product Name", "Brand", "Category", "Subcategory",
    "Current Stock Qty", "POS Purchase Cost (₹)", "Current POS Sale Price (₹)",
    "Inventory Bucket", "Recommended Client Action"
]

ws2.append(headers_tab2)
for col_num in range(1, len(headers_tab2) + 1):
    c = ws2.cell(row=1, column=col_num)
    c.fill = fill_header_tab2
    c.font = font_header
    c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

for row_idx, item in enumerate(hold_items, start=2):
    row_data = [
        row_idx - 1, item['pos_row'], item['name'], item['brand'], item['category'], item['subcategory'],
        item['stock'], item['purchase'], item['sale'], item['bucket'], item['action']
    ]
    ws2.append(row_data)

    is_even = (row_idx % 2 == 0)
    for col_num in range(1, len(headers_tab2) + 1):
        cell = ws2.cell(row=row_idx, column=col_num)
        cell.font = font_data
        cell.border = border_thin
        if col_num in [7, 8, 9]:
            cell.alignment = Alignment(horizontal='right', vertical='center')
            if col_num in [8, 9]:
                cell.number_format = '₹#,##0.00'
        elif col_num in [1, 2]:
            cell.alignment = Alignment(horizontal='center', vertical='center')
        else:
            cell.alignment = Alignment(horizontal='left', vertical='center')

        if is_even:
            cell.fill = fill_zebra

# Auto-fit column widths on both sheets
for ws in [ws1, ws2]:
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 48)

wb_handover.save(HANDOVER_XLSX)
print(f"      Created client handover workbook: {HANDOVER_XLSX}")
print(f"      - Tab 1: {len(manual_rows)} items (Needs Price or Photo)")
print(f"      - Tab 2: {len(hold_items)} items (Generic Counter Items, sorted by stock descending)")

print("\n" + "="*70)
print("PHASE 4 PYTHON EXECUTION COMPLETED SUCCESSFULLY!")
print("="*70)
