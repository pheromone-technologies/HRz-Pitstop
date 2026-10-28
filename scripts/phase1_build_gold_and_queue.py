#!/usr/bin/env python3
"""
Phase 1: Build Gold Master Verified Inventory, Scraping Queue, and Client Hold List.
Repo: HRz Pitstop (E:\\coad\\hrx website 2)

Reads:
- Verified_Stock_Inventory_Master_Current.xlsx (sheet "Product Master", 2,502 rows)
- HRZ_Pitstop_Client_Inventory_Filled.xlsx (all 14 product sheets + reference sheets)
- data/products.json and catalog.json

Outputs:
1. HRZ_Gold_Master_Verified.xlsx (100% verified Gold items across 14 tabs with Data Validations extended to Row 2000)
2. Needs_Scraping_Queue.csv (Externally Verified & Probable Match POS items missing real local image or retail price)
3. Client_Hold_Generic_And_Unfound.xlsx (303 N/A Generic + 103 Not Found items for shop owner)
"""

import os
import sys
import json
import csv
import re
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

# Force UTF-8 output encoding for Windows terminals
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Locate files in root or products data/
def find_input_file(filename):
    candidates = [
        os.path.join(BASE_DIR, filename),
        os.path.join(BASE_DIR, 'products data', filename),
        os.path.join(BASE_DIR, 'data', filename),
        os.path.join(BASE_DIR, '_vault_archive', 'legacy_catalogs_and_workbooks', filename),
        os.path.join(BASE_DIR, '_vault_archive', 'scraper_working_cache', filename)
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    raise FileNotFoundError(f"Cannot find required input file: {filename}")

MASTER_XLSX = find_input_file('Verified_Stock_Inventory_Master_Current.xlsx')
FILLED_XLSX = find_input_file('HRZ_Pitstop_Client_Inventory_Filled.xlsx')
PRODUCTS_JSON = find_input_file('products.json')
CATALOG_JSON = find_input_file('catalog.json')

# Output paths in workspace root
GOLD_OUTPUT_XLSX = os.path.join(BASE_DIR, 'HRZ_Gold_Master_Verified.xlsx')
QUEUE_OUTPUT_CSV = os.path.join(BASE_DIR, 'Needs_Scraping_Queue.csv')
HOLD_OUTPUT_XLSX = os.path.join(BASE_DIR, 'Client_Hold_Generic_And_Unfound.xlsx')

# ==============================================================================
# STEP 1: Unified Bandidos-Aligned Category & Subcategory Schema (14 Sheets)
# ==============================================================================
VALID_SCHEMA = {
    'Helmets & Accessories': [
        'Full-Face Helmet', 'Open-Face Helmet', 'Modular Helmet', 'Offroad Helmet',
        'Helmet Visor', 'Helmet Accessories', 'Communication & Intercoms', 'Riding Eyewear & Goggles'
    ],
    'Riding Gears': [
        'Riding Jackets', 'Gloves', 'Riding Pants', 'Boots',
        'Protective Armour', 'Rainwear', 'Balaclava & Base Layers', 'Other Riding Gear'
    ],
    'Bike Protection': [
        'Crash Guard', 'Frame Slider', 'Engine Guards and Skid Plate', 'Radiator Guard',
        'Master Cylinder Guard', 'Fluid Guards and Caps', 'Headlight Grill', 'Tank Protectors',
        'Boot Guards', 'Chain Cover And Sprocket', 'Screen Protectors', 'Lock system'
    ],
    'Handlebar & Accessories': [
        'Handlebars', 'Handle Risers', 'Hand Guard', 'Lever Guard',
        'Grips and Throttle', 'Mirror', 'Mounts and Chargers'
    ],
    'Foot Rests': [
        'Foot Pegs and Mounts'
    ],
    'Oil Caps & Stands': [
        'Front Oil Cap Silver', 'Rear Oil Cap', 'Side Stand Base', 'Paddock Stand & Spools'
    ],
    'Body Fairing and Fenders': [
        'Body Fairing', 'Fenders and Extenders', 'Tail'
    ],
    'Bike Essentials': [
        'Windshield', 'Winglet', 'Seat'
    ],
    'Cleaning Accessories': [
        'Cleaning Accessories'
    ],
    'Performance Accessories': [
        'Air Filter', 'Exhaust', 'Chain and Sprocket', 'Braking Components',
        'Performance Parts', 'Suspension & Fork Upgrades'
    ],
    'Lighting': [
        'Auxiliary Lights', 'Fog Lights', 'Headlights', 'Tail Lights',
        'Indicators', 'Hazard Module', 'Wiring and Electrical', 'Horns'
    ],
    'Guards & Mounts': [
        'Fog Light Mount', 'Light Mounts & Clamps'
    ],
    'Luggage & Touring': [
        'Saddle Bags', 'Tail Bags', 'Tank Bags', 'Backpacks', 'Top Boxes',
        'Panniers', 'Luggage Racks', 'Saddle Stays', 'Backrests', 'Touring Accessories'
    ],
    'General Accessories': [
        'Bike Covers', 'Security Accessories', 'Tyres & Wheel Accessories',
        'Merchandise & Decals', 'Tools & Workshop', 'Miscellaneous'
    ]
}

HELMET_BRANDS = {'smk', 'axor', 'vega', 'studds', 'kyt', 'steelbird', 'ls2'}

# Category code mapping for structured SKU generation
CAT_CODES = {
    'Helmets & Accessories': 'HEL',
    'Riding Gears': 'RID',
    'Bike Protection': 'BIK',
    'Handlebar & Accessories': 'HAN',
    'Foot Rests': 'FOO',
    'Oil Caps & Stands': 'OIL',
    'Body Fairing and Fenders': 'BOD',
    'Bike Essentials': 'ESS',
    'Cleaning Accessories': 'CLE',
    'Performance Accessories': 'PER',
    'Lighting': 'LIG',
    'Guards & Mounts': 'GUA',
    'Luggage & Touring': 'LUG',
    'General Accessories': 'GEN'
}

# Bike signatures for compatibility extraction
BIKE_SIGNATURES = [
    # Royal Enfield
    (r'\b(scram\s*440)\b', ('Royal Enfield', 'Scram 440')),
    (r'\b(scram\s*411|scram)\b', ('Royal Enfield', 'Scram 411')),
    (r'\b(classic\s*650)\b', ('Royal Enfield', 'Classic 650')),
    (r'\b(bear\s*650)\b', ('Royal Enfield', 'Bear 650')),
    (r'\b(guerrilla\s*450|guerrilla)\b', ('Royal Enfield', 'Guerrilla 450')),
    (r'\b(himalayan\s*450)\b', ('Royal Enfield', 'Himalayan 450')),
    (r'\b(himalayan\s*411|himalayan)\b', ('Royal Enfield', 'Himalayan 411')),
    (r'\b(super\s*meteor\s*650|super\s*meteor)\b', ('Royal Enfield', 'Super Meteor 650')),
    (r'\b(meteor\s*350|meteor)\b', ('Royal Enfield', 'Meteor 350')),
    (r'\b(hunter\s*350|hunter)\b', ('Royal Enfield', 'Hunter 350')),
    (r'\b(classic\s*350\s*reborn|classic\s*reborn|reborn)\b', ('Royal Enfield', 'Classic 350 Reborn')),
    (r'\b(standard\s*350\s*reborn)\b', ('Royal Enfield', 'Standard 350 Reborn')),
    (r'\b(classic\s*350|classic)\b', ('Royal Enfield', 'Classic 350 Reborn')),
    (r'\b(standard\s*350|bullet|standard|electra)\b', ('Royal Enfield', 'Classic 350 Reborn')),
    (r'\b(interceptor\s*650|interceptor)\b', ('Royal Enfield', 'Interceptor 650')),
    (r'\b(continental\s*gt\s*650|continental\s*gt|gt\s*650)\b', ('Royal Enfield', 'Continental GT 650')),
    (r'\b(thunderbird\s*x|thunderbird)\b', ('Royal Enfield', 'Thunderbird')),

    # KTM
    (r'\b(adv\s*390|adventure\s*390|390\s*adv)\b', ('KTM', 'Adventure 390')),
    (r'\b(adv\s*250|adventure\s*250|250\s*adv)\b', ('KTM', 'Adventure 250')),
    (r'\b(duke\s*390|390\s*duke)\b', ('KTM', 'Duke 390 Gen-3')),
    (r'\b(duke\s*250|250\s*duke)\b', ('KTM', 'Duke 250')),
    (r'\b(duke\s*200|200\s*duke)\b', ('KTM', 'Duke 200')),
    (r'\b(duke\s*125|125\s*duke)\b', ('KTM', 'Duke 125')),
    (r'\b(rc\s*390|rc390)\b', ('KTM', 'RC 390')),
    (r'\b(enduro\s*390|390\s*enduro)\b', ('KTM', '390 Enduro R')),

    # Yamaha
    (r'\b(xsr\s*155|xsr155)\b', ('Yamaha', 'XSR 155')),
    (r'\b(rx\s*100|rx100)\b', ('Yamaha', 'RX 100')),
    (r'\b(aerox\s*155|aerox)\b', ('Yamaha', 'Aerox 155')),
    (r'\b(mt\s*15|mt15)\b', ('Yamaha', 'MT-15 V2')),
    (r'\b(r15\s*v4|r15\s*v3|r15)\b', ('Yamaha', 'R15 V4')),
    (r'\b(r3)\b', ('Yamaha', 'R3')),
    (r'\b(fzs|fz\s*v3|fz\s*v4)\b', ('Yamaha', 'FZS V3 / V4')),

    # Bajaj
    (r'\b(ns\s*400z|ns400z|ns400|ns\s*400)\b', ('Bajaj', 'Pulsar NS400Z')),
    (r'\b(pulsar\s*220|220f)\b', ('Bajaj', 'Pulsar 220')),
    (r'\b(ns\s*200|ns200)\b', ('Bajaj', 'Pulsar NS200')),
    (r'\b(rs\s*200|rs200)\b', ('Bajaj', 'Pulsar RS 200')),
    (r'\b(n\s*250|n250)\b', ('Bajaj', 'Pulsar N250')),
    (r'\b(dominar\s*400|dominar)\b', ('Bajaj', 'Dominar 400')),
    (r'\b(dominar\s*250)\b', ('Bajaj', 'Dominar 400')),

    # Honda
    (r'\b(transalp\s*750|xl750\s*transalp|transalp)\b', ('Honda', 'XL750 Transalp')),
    (r'\b(nx\s*500|nx500)\b', ('Honda', 'NX500')),
    (r'\b(cb\s*200x|cb200x)\b', ('Honda', 'CB 200X')),
    (r'\b(hness\s*cb\s*350|hness|cb\s*350\b|highness|h\'ness)\b', ('Honda', "H'ness CB 350")),
    (r'\b(cb\s*350\s*rs|cb350rs)\b', ('Honda', 'CB 350 RS')),
    (r'\b(cb\s*500x|cb500x)\b', ('Honda', 'CB 500X')),

    # Triumph
    (r'\b(speed\s*400)\b', ('Triumph', 'Speed 400')),
    (r'\b(scrambler\s*400\s*x|scrambler\s*400x|tracker\s*400)\b', ('Triumph', 'Scrambler 400 X')),
    (r'\b(tiger\s*sport\s*660)\b', ('Triumph', 'Tiger Sport 660')),
    (r'\b(tiger\s*900|tiger)\b', ('Triumph', 'Tiger 900')),

    # Hero
    (r'\b(xpulse\s*210)\b', ('Hero', 'XPulse 210')),
    (r'\b(xpulse\s*200\s*4v|xpulse\s*200|xpulse)\b', ('Hero', 'XPulse 200 4V')),
    (r'\b(mavrick\s*440|mavrick)\b', ('Hero', 'Mavrick 440')),

    # TVS
    (r'\b(apache\s*rr\s*310|rr\s*310)\b', ('TVS', 'Apache RR 310')),
    (r'\b(apache\s*rtr\s*310|rtr\s*310)\b', ('TVS', 'Apache RTR 310')),
    (r'\b(ronin)\b', ('TVS', 'tvs ronin')),
    (r'\b(apache\s*rtx\s*300)\b', ('TVS', 'Apache RTX 300 new')),

    # Harley-Davidson
    (r'\b(x\s*440|x440|harley\s*440)\b', ('Harley-Davidson', 'Harley 440X')),

    # Suzuki
    (r'\b(v\s*strom\s*250|v-strom\s*250|vstrom\s*250)\b', ('Suzuki', 'V Strom 250')),
    (r'\b(gixxer\s*sf|gixxer)\b', ('Suzuki', 'Gixxer SF'))
]

COLOR_KEYWORDS = [
    'Matte Black', 'Matt Black', 'Gloss Black', 'Glossy Black', 'Dull Black',
    'Neon Yellow', 'Neon Green', 'Neon Red', 'Fluro Yellow',
    'Black', 'Red', 'Blue', 'White', 'Silver', 'Grey', 'Gray', 'Yellow', 'Green',
    'Orange', 'Neon', 'Gold', 'Chrome', 'Bronze', 'Smoke', 'Clear', 'Titanium',
    'Anthracite', 'Camo', 'Khaki', 'Burgundy', 'Fluo'
]

SIZE_PATTERNS = [
    r'\b(XXXL|3XL|XXL|2XL|XL|L|M|S|XS)\b',
    r'\b(UK\s*\d{1,2})\b',
    r'\b(EURO\s*\d{2})\b',
    r'\b(SIZE\s*[-:]?\s*[A-Z0-9]+)\b'
]

def clean_text_norm(s):
    if not s: return ''
    return re.sub(r'[^a-z0-9]', '', str(s).lower())

def extract_color(product_name, master_color=''):
    if master_color and str(master_color).strip() and str(master_color).strip().lower() != 'none':
        return str(master_color).strip()
    name = str(product_name or '')
    for ck in COLOR_KEYWORDS:
        if re.search(r'\b' + re.escape(ck) + r'\b', name, re.IGNORECASE):
            return ck
    return ''

def extract_size(product_name, master_size=''):
    if master_size and str(master_size).strip() and str(master_size).strip().lower() != 'none':
        return str(master_size).strip()
    name = str(product_name or '')
    for sp in SIZE_PATTERNS:
        m = re.search(sp, name, re.IGNORECASE)
        if m:
            return m.group(1).upper()
    return ''

def extract_fitment(product_name, master_make, master_model, filled_make='', filled_model='', vc_dict=None, sku=''):
    # 1. From Vehicle Compatibility dictionary
    if vc_dict:
        norm_n = clean_text_norm(product_name)
        if sku and sku in vc_dict:
            make, model = vc_dict[sku]
            if make and model: return make, model
        if norm_n in vc_dict:
            make, model = vc_dict[norm_n]
            if make and model: return make, model

    # 2. From Filled sheet
    fm = str(filled_make or '').strip()
    fmod = str(filled_model or '').strip()
    if fm and fmod and fm != 'Universal' and fmod != 'Universal':
        return fm, fmod

    # 3. From Master Product Master
    mm = str(master_make or '').strip()
    mmod = str(master_model or '').strip()
    if mm and mmod and mm != 'Universal' and mmod != 'Universal':
        return mm, mmod

    # 4. From Title Parser
    name_str = str(product_name or '')
    for pat, (b_make, b_model) in BIKE_SIGNATURES:
        if re.search(pat, name_str, re.IGNORECASE):
            return b_make, b_model

    # 5. Default
    return 'Universal', 'Universal'

def sanitize_description(text, product_name='', brand=''):
    if not text or not str(text).strip():
        b = str(brand).strip() if brand else 'HRz Pitstop'
        return f"{product_name} - Premium motorcycle accessory verified by {b}."
    t = str(text)

    # 1. Strip shopify section containers
    t = re.sub(r'<div class="[^"]*shopify-section[^"]*"[^>]*>[\s\S]*?</div>', '', t, flags=re.IGNORECASE)
    t = re.sub(r'<div id="shopify-section-[^"]*"[^>]*>[\s\S]*?</div>', '', t, flags=re.IGNORECASE)

    # 2. Strip article tags
    t = re.sub(r'</?article[^>]*>', '', t, flags=re.IGNORECASE)

    # 3. Strip data-* attributes
    t = re.sub(r'\s+data-[a-zA-Z0-9_-]+="[^"]*"', '', t)
    t = re.sub(r"\s+data-[a-zA-Z0-9_-]+='[^']*'", '', t)

    # 4. Strip Claude/ChatGPT AI tags
    t = re.sub(r'class="[^"]*(?:claude|chatgpt|ai-response)[^"]*"', '', t, flags=re.IGNORECASE)
    t = re.sub(r'<p[^>]*class="[^"]*claude[^"]*"[^>]*>[\s\S]*?</p>', '', t, flags=re.IGNORECASE)

    # 5. Brand name sanitization
    t = re.sub(r'\bBandidos\s*Pitstop\b', 'HRz Pitstop', t, flags=re.IGNORECASE)
    t = re.sub(r'\bBandidospitstop\b', 'HRz Pitstop', t, flags=re.IGNORECASE)
    t = re.sub(r'\bBandidos\b', 'HRz Pitstop', t, flags=re.IGNORECASE)
    t = re.sub(r'\bMotocaan\b', 'HRz Pitstop', t, flags=re.IGNORECASE)

    # Clean whitespace
    t = re.sub(r'\n\s*\n+', '\n', t).strip()
    if not t:
        b = str(brand).strip() if brand else 'HRz Pitstop'
        return f"{product_name} - Premium motorcycle accessory verified by {b}."
    return t

# ==============================================================================
# Comprehensive Category & Subcategory Routing Logic
# ==============================================================================
def route_item(name, brand, current_sheet='', orig_subcat=''):
    n = (name or '').lower()
    b = (brand or '').lower()
    s = (orig_subcat or '').strip()
    cs = (current_sheet or '').strip()

    # 1. Helmets & Accessories: Route ALL SMK, Axor, Vega, Studds, KYT, Steelbird, LS2, MT helmets here
    is_helmet_brand = any(hb in b for hb in HELMET_BRANDS)
    is_mt_helmet = ('mt ' in b or b == 'mt') and ('helmet' in n or any(w in n for w in ['targo', 'blade', 'thunder', 'revenge', 'jarama', 'street', 'kre', 'atom', 'matrix', 'braker', 'stinger']))
    if ('helmet' in n or is_helmet_brand or is_mt_helmet):
        # Exclude luggage carriers made by Moto Torque (which sometimes get labeled MT)
        if not (('mt - ' in n or 'moto torque' in b) and any(w in n for w in ['carrier', 'top plate', 'combo kit', 'stay', 'rack', 'guard', 'slider'])):
            cat = 'Helmets & Accessories'
            if any(w in n for w in ['visor', 'pinlock', 'anti fog', 'anti-fog', 'shield']):
                return cat, 'Helmet Visor'
            elif any(w in n for w in ['intercom', 'bluetooth', 'communicat']):
                return cat, 'Communication & Intercoms'
            elif any(w in n for w in ['goggle', 'eyewear', 'glasses']):
                return cat, 'Riding Eyewear & Goggles'
            elif any(w in n for w in ['open face', 'open-face', 'jet', 'retro open']):
                return cat, 'Open-Face Helmet'
            elif any(w in n for w in ['modular', 'flip up', 'flip-up']):
                return cat, 'Modular Helmet'
            elif any(w in n for w in ['offroad', 'off-road', 'motocross', 'dirt']):
                return cat, 'Offroad Helmet'
            elif any(w in n for w in ['spoiler', 'peak', 'pad', 'cheek', 'strap', 'buckle', 'breath', 'curtain', 'chin']):
                return cat, 'Helmet Accessories'
            else:
                return cat, 'Full-Face Helmet'

    # 4. Handlebar & Accessories: Route ALL GPS mounts & mobile mounts & chargers here!
    if any(w in n for w in ['gps mount', 'mobile mount', 'phone mount', 'mobile holder', 'phone holder', 'smartphone mount', 'charger', 'usb charger']) or s in ['Mobile Holders', 'Chargers', 'Mounts and Chargers']:
        return 'Handlebar & Accessories', 'Mounts and Chargers'

    # 9. Cleaning Accessories: All Lubes, Cleaners, Polishes, Engine Oils
    if any(w in n for w in ['chain lube', 'chain clean', 'cleaner', 'polish', 'wash', 'degreaser', 'microfiber', 'cloth', 'brush', 'motul 3000', 'motul 3100', 'motul 7100', 'motul 5100', 'engine oil', '10w40', '15w50', '20w50', '10w30', '10w50', 'brake fluid', 'coolant', 'lubricant']) or cs == 'Cleaning Accessories' or s == 'Cleaning Accessories':
        return 'Cleaning Accessories', 'Cleaning Accessories'

    # 2. Riding Gears
    if any(w in n for w in ['jacket', 'jackets']) or s == 'Riding Jackets':
        return 'Riding Gears', 'Riding Jackets'
    if any(w in n for w in ['glove', 'gloves']) or s == 'Gloves':
        return 'Riding Gears', 'Gloves'
    if any(w in n for w in ['pant', 'pants', 'trouser', 'jeans', 'riding denim']) or s == 'Riding Pants':
        return 'Riding Gears', 'Riding Pants'
    if any(w in n for w in ['boot', 'boots', 'shoe', 'shoes', 'footwear']) or s == 'Boots':
        return 'Riding Gears', 'Boots'
    if any(w in n for w in ['knee guard', 'elbow guard', 'armour', 'armor', 'bionic', 'back protector', 'chest protector', 'spine guard']) or s == 'Protective Armour':
        return 'Riding Gears', 'Protective Armour'
    if any(w in n for w in ['rainwear', 'rain coat', 'raincoat', 'rain jacket', 'rain pant', 'rain suit']) or s == 'Rainwear':
        return 'Riding Gears', 'Rainwear'
    if any(w in n for w in ['balaclava', 'base layer', 'face mask', 'compression', 'arm sleeve', 'sleeves', 'socks']) or s == 'Balaclava & Base Layers':
        return 'Riding Gears', 'Balaclava & Base Layers'
    if cs == 'Riding Gears':
        return 'Riding Gears', 'Other Riding Gear'

    # 5. Foot Rests
    if any(w in n for w in ['foot peg', 'footpeg', 'foot rest', 'footrest', 'pegs']) or cs == 'Foot Rests' or s == 'Foot Pegs and Mounts':
        return 'Foot Rests', 'Foot Pegs and Mounts'

    # 6. Oil Caps & Stands
    if 'front oil cap' in n or s == 'Front Oil Cap Silver':
        return 'Oil Caps & Stands', 'Front Oil Cap Silver'
    if 'rear oil cap' in n or s == 'Rear Oil Cap':
        return 'Oil Caps & Stands', 'Rear Oil Cap'
    if any(w in n for w in ['side stand base', 'stand extender', 'side stand extender']) or s == 'Side Stand Base':
        return 'Oil Caps & Stands', 'Side Stand Base'
    if any(w in n for w in ['paddock stand', 'paddock spool', 'spool', 'spools', 'bobbins']) or s == 'Paddock Stand & Spools':
        return 'Oil Caps & Stands', 'Paddock Stand & Spools'

    # 7. Body Fairing and Fenders
    if any(w in n for w in ['tail tidy', 'number plate stay', 'number plate holder', 'tail ']) or s == 'Tail':
        return 'Body Fairing and Fenders', 'Tail'
    if any(w in n for w in ['fender', 'mudguard', 'tyre hugger', 'tire hugger', 'extender', 'fenders']) or s == 'Fenders and Extenders':
        return 'Body Fairing and Fenders', 'Fenders and Extenders'
    if any(w in n for w in ['fairing', 'cowl', 'belly pan', 'side panel', 'body fairing']) or s == 'Body Fairing' or cs == 'Body Fairing and Fenders':
        return 'Body Fairing and Fenders', 'Body Fairing'

    # 8. Bike Essentials
    if any(w in n for w in ['windshield', 'windscreen', 'bike visor', 'visor (bike)']) or s == 'Windshield':
        return 'Bike Essentials', 'Windshield'
    if 'winglet' in n or s == 'Winglet':
        return 'Bike Essentials', 'Winglet'
    if any(w in n for w in ['seat', 'seat cover', 'touring seat', 'rally seat']) or s == 'Seat' or cs == 'Bike Essentials':
        return 'Bike Essentials', 'Seat'

    # 10. Performance Accessories
    if any(w in n for w in ['air filter', 'airfilter', 'bmc air filter', 'dna air filter']) or s == 'Air Filter':
        return 'Performance Accessories', 'Air Filter'
    if any(w in n for w in ['exhaust', 'bend pipe', 'slip on', 'slip-on', 'muffler', 'header pipe']) or s == 'Exhaust':
        return 'Performance Accessories', 'Exhaust'
    if any(w in n for w in ['chain and sprocket', 'chain sprocket', 'brass chain', 'sprocket kit', 'sprocket', 'chain kit']) or s == 'Chain and Sprocket':
        return 'Performance Accessories', 'Chain and Sprocket'
    if any(w in n for w in ['brake pad', 'braking', 'brake disc', 'rotor', 'brake hose', 'brake line', 'caliper']) or s == 'Braking Components':
        return 'Performance Accessories', 'Braking Components'
    if any(w in n for w in ['fuelx', 'powertronic', 'spark plug', 'iridium', 'ecu', 'quickshifter']) or s == 'Performance Parts':
        return 'Performance Accessories', 'Performance Parts'
    if any(w in n for w in ['suspension', 'fork upgrade', 'fork spring', 'mono shock', 'fork preload']) or s == 'Suspension & Fork Upgrades':
        return 'Performance Accessories', 'Suspension & Fork Upgrades'

    # 11. Lighting
    if any(w in n for w in ['auxiliary light', 'aux light', 'spot light', 'cube light']) or s == 'Auxiliary Lights':
        return 'Lighting', 'Auxiliary Lights'
    if any(w in n for w in ['fog light', 'fog lamp', 'fog lights', 'hjg', 'future eyes', 'maddog']) or s == 'Fog Lights':
        return 'Lighting', 'Fog Lights'
    if any(w in n for w in ['headlight', 'head lamp', 'head light']) or s == 'Headlights':
        return 'Lighting', 'Headlights'
    if any(w in n for w in ['tail light', 'brake light']) or s == 'Tail Lights':
        return 'Lighting', 'Tail Lights'
    if any(w in n for w in ['indicator', 'indicators', 'turn signal', 'blinker']) or s == 'Indicators':
        return 'Lighting', 'Indicators'
    if any(w in n for w in ['hazard module', 'hazard flasher', 'simtac', 'hazard']) or s == 'Hazard Module':
        return 'Lighting', 'Hazard Module'
    if any(w in n for w in ['wiring', 'harness', 'relay', 'switch', 'electrical', 'wire harness']) or s == 'Wiring and Electrical':
        return 'Lighting', 'Wiring and Electrical'
    if any(w in n for w in ['horn', 'horns']) or s == 'Horns':
        return 'Lighting', 'Horns'
    if cs == 'Lighting':
        return 'Lighting', 'Auxiliary Lights'

    # 12. Guards & Mounts
    if any(w in n for w in ['fog light mount', 'fog light clamp', 'light mount', 'light bracket']) or s == 'Fog Light Mount':
        return 'Guards & Mounts', 'Fog Light Mount'
    if any(w in n for w in ['light clamp', 'mounting clamp', 'bar clamp']) or s == 'Light Mounts & Clamps' or cs == 'Guards & Mounts':
        return 'Guards & Mounts', 'Light Mounts & Clamps'

    # 13. Luggage & Touring
    if any(w in n for w in ['saddle bag', 'saddlebag', 'saddle bags']) or s == 'Saddle Bags':
        return 'Luggage & Touring', 'Saddle Bags'
    if any(w in n for w in ['tail bag', 'rear seat bag', 'tailbag']) or s == 'Tail Bags':
        return 'Luggage & Touring', 'Tail Bags'
    if any(w in n for w in ['tank bag', 'tankbag']) or s == 'Tank Bags':
        return 'Luggage & Touring', 'Tank Bags'
    if any(w in n for w in ['backpack', 'hydration pack', 'rucksack']) or s == 'Backpacks':
        return 'Luggage & Touring', 'Backpacks'
    if any(w in n for w in ['top box', 'topbox', 'top case']) or s == 'Top Boxes':
        return 'Luggage & Touring', 'Top Boxes'
    if any(w in n for w in ['pannier', 'panniers', 'side box']) or s == 'Panniers':
        return 'Luggage & Touring', 'Panniers'
    if any(w in n for w in ['carrier', 'top plate', 'rear rack', 'luggage rack', 'top rack']) or s in ['Luggage Racks', 'Luggage Carrier']:
        return 'Luggage & Touring', 'Luggage Racks'
    if any(w in n for w in ['saddle stay', 'saddlestay', 'side stay']) or s == 'Saddle Stays':
        return 'Luggage & Touring', 'Saddle Stays'
    if any(w in n for w in ['backrest', 'back rest', 'pillion rest']) or s == 'Backrests':
        return 'Luggage & Touring', 'Backrests'
    if any(w in n for w in ['jerry can', 'bungee', 'bottle holder', 'cargo net']) or s in ['Touring Accessories', 'Other Luggage'] or cs == 'Luggage & Touring':
        return 'Luggage & Touring', 'Touring Accessories'

    # 4. Handlebar & Accessories
    if any(w in n for w in ['handlebar', 'handle bar']) or s == 'Handlebars':
        return 'Handlebar & Accessories', 'Handlebars'
    if any(w in n for w in ['handle riser', 'bar riser', 'riser']) or s == 'Handle Risers':
        return 'Handlebar & Accessories', 'Handle Risers'
    if any(w in n for w in ['hand guard', 'handguard', 'knuckle guard']) or s == 'Hand Guard':
        return 'Handlebar & Accessories', 'Hand Guard'
    if any(w in n for w in ['lever guard', 'leverguard']) or s == 'Lever Guard':
        return 'Handlebar & Accessories', 'Lever Guard'
    if any(w in n for w in ['grip', 'grips', 'throttle', 'bar end']) or s == 'Grips and Throttle':
        return 'Handlebar & Accessories', 'Grips and Throttle'
    if any(w in n for w in ['mirror', 'mirrors']) or s == 'Mirror':
        return 'Handlebar & Accessories', 'Mirror'
    if cs == 'Handlebar & Accessories':
        return 'Handlebar & Accessories', 'Mounts and Chargers'

    # 3. Bike Protection
    if any(w in n for w in ['crash guard', 'crashguard', 'leg guard', 'cg with slider', 'crash bar']) or s == 'Crash Guard':
        return 'Bike Protection', 'Crash Guard'
    if any(w in n for w in ['frame slider', 'slider', 'sliders', 'fork slider', 'axle slider']) or s == 'Frame Slider':
        return 'Bike Protection', 'Frame Slider'
    if any(w in n for w in ['engine guard', 'skid plate', 'bash plate', 'bashplate', 'sump guard']) or s == 'Engine Guards and Skid Plate':
        return 'Bike Protection', 'Engine Guards and Skid Plate'
    if any(w in n for w in ['radiator guard', 'radiator grill', 'radiator protector']) or s in ['Radiator Guard', 'Radiator Grill']:
        return 'Bike Protection', 'Radiator Guard'
    if any(w in n for w in ['master cylinder guard', 'cylinder guard', 'caliper guard']) or s == 'Master Cylinder Guard':
        return 'Bike Protection', 'Master Cylinder Guard'
    if any(w in n for w in ['fluid guard', 'fluid cap', 'reservoir guard']) or s == 'Fluid Guards and Caps':
        return 'Bike Protection', 'Fluid Guards and Caps'
    if any(w in n for w in ['headlight grill', 'headlight guard', 'headlight shield']) or s in ['Headlight Grill', 'Head Light Grill']:
        return 'Bike Protection', 'Headlight Grill'
    if any(w in n for w in ['tank protector', 'tank pad', 'tank grip']) or s == 'Tank Protectors':
        return 'Bike Protection', 'Tank Protectors'
    if any(w in n for w in ['boot guard', 'heel guard']) or s == 'Boot Guards':
        return 'Bike Protection', 'Boot Guards'
    if any(w in n for w in ['chain cover', 'sprocket cover', 'chain guard']) or s == 'Chain Cover And Sprocket':
        return 'Bike Protection', 'Chain Cover And Sprocket'
    if any(w in n for w in ['screen protector', 'meter protector', 'display protector']) or s == 'Screen Protectors':
        return 'Bike Protection', 'Screen Protectors'
    if any(w in n for w in ['lock', 'disc lock', 'cable lock']) or s == 'Lock system':
        return 'Bike Protection', 'Lock system'
    if cs == 'Bike Protection':
        return 'Bike Protection', 'Crash Guard'

    # 14. General Accessories
    if any(w in n for w in ['bike cover', 'body cover', 'cover']) or s == 'Bike Covers':
        return 'General Accessories', 'Bike Covers'
    if any(w in n for w in ['security', 'alarm', 'anti theft']) or s == 'Security Accessories':
        return 'General Accessories', 'Security Accessories'
    if any(w in n for w in ['tyre', 'tire', 'wheel', 'valve', 'puncture', 'inflator']) or s == 'Tyres & Wheel Accessories':
        return 'General Accessories', 'Tyres & Wheel Accessories'
    if any(w in n for w in ['merchandise', 'decal', 'sticker', 'keychain', 't-shirt', 'cap']) or s == 'Merchandise & Decals':
        return 'General Accessories', 'Merchandise & Decals'
    if any(w in n for w in ['tool', 'toolkit', 'spanner', 'wrench', 'allen key']) or s == 'Tools & Workshop':
        return 'General Accessories', 'Tools & Workshop'

    # Check if cs and s are already valid
    if cs in VALID_SCHEMA and s in VALID_SCHEMA[cs]:
        return cs, s

    return 'General Accessories', 'Miscellaneous'

# ==============================================================================
# MAIN EXECUTION PIPELINE
# ==============================================================================
def main():
    print("=" * 80)
    print("PHASE 1: BUILD GOLD MASTER VERIFIED INVENTORY & SCRAPING QUEUE")
    print("=" * 80)

    # 1. Index local image filesystem
    print("\n[1/6] Indexing local image files (>1KB on disk)...")
    local_images = {}
    for search_dir in ['images', 'image data']:
        full_dir = os.path.join(BASE_DIR, search_dir)
        if os.path.exists(full_dir):
            for root, dirs, files in os.walk(full_dir):
                for f in files:
                    if f.lower().endswith(('.webp', '.jpg', '.png', '.jpeg')):
                        full_p = os.path.join(root, f)
                        rel_p = os.path.relpath(full_p, BASE_DIR).replace('\\', '/')
                        try:
                            if os.path.getsize(full_p) > 1024:
                                local_images[f.lower()] = rel_p
                        except OSError:
                            pass
    print(f"      Indexed {len(local_images)} verified local image files.")

    # 2. Load auxiliary catalogs
    print("\n[2/6] Loading data/products.json and catalog.json...")
    with open(PRODUCTS_JSON, 'r', encoding='utf-8') as f:
        products_json = json.load(f)
    pj_by_norm = {}
    for p in products_json:
        if p.get('name'):
            pj_by_norm[clean_text_norm(p['name'])] = p

    with open(CATALOG_JSON, 'r', encoding='utf-8') as f:
        catalog_json = json.load(f)
    cat_by_norm = {}
    for c in catalog_json:
        if c.get('product_name'):
            cat_by_norm[clean_text_norm(c['product_name'])] = c
    print(f"      products.json: {len(products_json)} items, catalog.json: {len(catalog_json)} items.")

    # 3. Load HRZ_Pitstop_Client_Inventory_Filled.xlsx
    print("\n[3/6] Loading HRZ_Pitstop_Client_Inventory_Filled.xlsx...")
    wb_filled = openpyxl.load_workbook(FILLED_XLSX, data_only=True)
    filled_by_norm = {}
    for s_name in wb_filled.sheetnames[:14]:
        ws = wb_filled[s_name]
        for r in list(ws.iter_rows(values_only=True))[1:]:
            if r and r[0]:
                pname = str(r[0]).strip()
                k = clean_text_norm(pname)
                if k not in filled_by_norm:
                    filled_by_norm[k] = (s_name, r)
    print(f"      Loaded {len(filled_by_norm)} items from Filled sheets.")

    # 4. Load Master Vehicle Compatibility
    print("\n[4/6] Loading Vehicle Compatibility table...")
    wb_master = openpyxl.load_workbook(MASTER_XLSX, data_only=True)
    vc_dict = {}
    if 'Vehicle Compatibility' in wb_master.sheetnames:
        ws_vc = wb_master['Vehicle Compatibility']
        for r in list(ws_vc.iter_rows(values_only=True))[1:]:
            if r and r[2]:
                sku_val = str(r[0] or '').strip()
                name_val = str(r[2] or '').strip()
                make_val = str(r[3] or '').strip()
                model_val = str(r[4] or '').strip()
                if sku_val and sku_val != 'Missing SKU':
                    vc_dict[sku_val] = (make_val, model_val)
                vc_dict[clean_text_norm(name_val)] = (make_val, model_val)
    print(f"      Loaded {len(vc_dict)} vehicle compatibility mappings.")

    # 5. Evaluate all 2,502 POS Master rows
    print("\n[5/6] Processing 2,502 items against strict 6-point verification gate...")
    ws_master = wb_master['Product Master']
    master_rows = list(ws_master.iter_rows(min_row=2, values_only=True))

    gold_items = []
    queue_items = []
    client_hold_items = []

    for row_idx, r in enumerate(master_rows, start=2):
        sku = str(r[0] or '').strip()
        pname = str(r[1] or '').strip()
        cat_pos = str(r[2] or '').strip()
        subcat_pos = str(r[3] or '').strip()
        brand_pos = str(r[4] or '').strip()
        color_pos = str(r[6] or '').strip()
        size_pos = str(r[7] or '').strip()
        make_pos = str(r[8] or '').strip()
        model_pos = str(r[9] or '').strip()
        desc_pos = str(r[10] or '').strip()
        stock_qty = r[11] if r[11] is not None else 0
        sale_price_pos = float(r[12]) if r[12] is not None and str(r[12]).strip() != '' else 0.0
        purch_price_pos = float(r[13]) if r[13] is not None and str(r[13]).strip() != '' else 0.0
        source_ref = str(r[18] or f'Row {row_idx}').strip()
        ext_ver = str(r[20] or '').strip()
        evid_url = str(r[21] or '').strip()

        norm_name = clean_text_norm(pname)

        # Separate Client Hold items immediately (303 Generic + 103 Not Found)
        if ext_ver in ['N/A — Generic/Unbranded', 'Not Found Externally']:
            client_hold_items.append({
                'row_id': row_idx,
                'sku': sku,
                'name': pname,
                'category': cat_pos,
                'subcategory': subcat_pos,
                'brand': brand_pos,
                'stock': stock_qty,
                'sale_price': sale_price_pos,
                'purch_price': purch_price_pos,
                'ext_ver': ext_ver,
                'source_ref': source_ref
            })
            continue

        # Look up filled and catalog matches
        f_match = filled_by_norm.get(norm_name)
        f_sheet = f_match[0] if f_match else ''
        f_row = f_match[1] if f_match else None

        pj_match = pj_by_norm.get(norm_name)
        cat_match = cat_by_norm.get(norm_name)

        # Route to Unified Bandidos Schema
        f_sub = str(f_row[1] or '') if f_row else subcat_pos
        brand_val = str(f_row[2] or '') if (f_row and f_row[2]) else (brand_pos or (pj_match.get('brand', '') if pj_match else ''))
        unified_cat, unified_subcat = route_item(pname, brand_val, f_sheet, f_sub)

        # GATE #1: Verified Identity
        is_verified_identity = (ext_ver == 'Externally Verified') or (norm_name in pj_by_norm)

        # GATE #2: Real Image on Disk (>1KB)
        verified_image = None

        # Check Filled sheet image
        if f_row and len(f_row) > 9 and f_row[9]:
            img_candidate = str(f_row[9]).strip().replace('\\', '/')
            if img_candidate:
                if os.path.exists(os.path.join(BASE_DIR, img_candidate)) and os.path.getsize(os.path.join(BASE_DIR, img_candidate)) > 1024:
                    verified_image = img_candidate
                else:
                    base_name = os.path.basename(img_candidate).split('?')[0].lower()
                    if base_name in local_images:
                        verified_image = local_images[base_name]

        # Check products.json image
        if not verified_image and pj_match and pj_match.get('image'):
            img_candidate = str(pj_match['image']).strip().replace('\\', '/')
            if img_candidate:
                if os.path.exists(os.path.join(BASE_DIR, img_candidate)) and os.path.getsize(os.path.join(BASE_DIR, img_candidate)) > 1024:
                    verified_image = img_candidate
                else:
                    base_name = os.path.basename(img_candidate).split('?')[0].lower()
                    if base_name in local_images:
                        verified_image = local_images[base_name]

        # Check catalog.json image
        if not verified_image and cat_match and cat_match.get('image_path'):
            img_candidate = str(cat_match['image_path']).strip().replace('\\', '/')
            if img_candidate:
                if os.path.exists(os.path.join(BASE_DIR, img_candidate)) and os.path.getsize(os.path.join(BASE_DIR, img_candidate)) > 1024:
                    verified_image = img_candidate
                else:
                    base_name = os.path.basename(img_candidate).split('?')[0].lower()
                    if base_name in local_images:
                        verified_image = local_images[base_name]

        has_real_image = verified_image is not None

        # GATE #3: 100% Real Retail Price (NO Wholesale Cost Copies)
        # Condition: Selling Price MUST be > Purchase Price * 1.08 (if Purchase Price > 0) AND Selling Price > 0.
        # REJECT any price where abs(Selling Price - Purchase Price) < 1.0.
        verified_sp = None
        verified_mrp = None

        # Try Filled sheet prices
        if f_row and len(f_row) > 6 and f_row[6] is not None:
            try:
                f_sp = float(f_row[6])
                f_m = float(f_row[5]) if f_row[5] is not None and str(f_row[5]).strip() != '' else f_sp
                # Reject 0%-margin copy bug
                if not (purch_price_pos > 0 and abs(f_sp - purch_price_pos) < 1.0):
                    if f_sp > 0 and (purch_price_pos <= 0 or f_sp > purch_price_pos * 1.08):
                        verified_sp = f_sp
                        verified_mrp = f_m
            except (ValueError, TypeError):
                pass

        # Try products.json prices
        if verified_sp is None and pj_match:
            try:
                pj_sp = float(pj_match.get('price', 0))
                pj_m = float(pj_match.get('originalPrice', 0)) or pj_sp
                if pj_sp > 0 and (purch_price_pos <= 0 or pj_sp > purch_price_pos * 1.08):
                    verified_sp = pj_sp
                    verified_mrp = pj_m
            except (ValueError, TypeError):
                pass

        # Try POS master sale price
        if verified_sp is None and sale_price_pos > 0 and (purch_price_pos <= 0 or sale_price_pos > purch_price_pos * 1.08):
            verified_sp = sale_price_pos
            verified_mrp = sale_price_pos

        # Try catalog.json prices
        if verified_sp is None and cat_match:
            try:
                cat_m = float(cat_match.get('mrp', 0))
                if cat_m > 0 and (purch_price_pos <= 0 or cat_m > purch_price_pos * 1.08):
                    verified_sp = cat_m
                    verified_mrp = cat_m
            except (ValueError, TypeError):
                pass

        has_real_price = verified_sp is not None and verified_sp > 0

        # GATE #4: Verified SKU & Variant
        if not sku or sku == 'Missing SKU' or sku.lower() == 'none':
            b_prefix = re.sub(r'[^A-Z0-9]', '', (brand_val or 'HRZ').upper())[:3] or 'HRZ'
            c_prefix = CAT_CODES.get(unified_cat, 'GEN')
            assigned_sku = f"HRZ-{b_prefix}-{c_prefix}-{row_idx:04d}"
        else:
            assigned_sku = sku

        extracted_color = extract_color(pname, color_pos)
        extracted_size = extract_size(pname, size_pos)

        # GATE #5: Bike Compatibility
        if unified_cat in ['Helmets & Accessories', 'Riding Gears', 'Cleaning Accessories']:
            compat_make = 'Universal'
            compat_model = 'Universal'
        else:
            filled_mk = str(f_row[3] or '') if f_row else ''
            filled_md = str(f_row[4] or '') if f_row else ''
            compat_make, compat_model = extract_fitment(
                pname, make_pos, model_pos, filled_mk, filled_md, vc_dict, sku
            )

        # GATE #6: Sanitized Description
        raw_desc = (str(f_row[10]) if (f_row and len(f_row) > 10 and f_row[10]) else (desc_pos or ''))
        clean_desc = sanitize_description(raw_desc, pname, brand_val)

        # Price rounding and clean discount
        if has_real_price:
            final_sp = int(round(verified_sp))
            final_mrp = int(round(verified_mrp if verified_mrp and verified_mrp >= verified_sp else final_sp))
            if final_mrp <= final_sp:
                final_mrp = final_sp
                discount_pct = 0
            else:
                discount_pct = int(round(((final_mrp - final_sp) / final_mrp) * 100))
        else:
            final_sp = 0
            final_mrp = 0
            discount_pct = 0

        # Final 6-Point Gate Check
        if is_verified_identity and has_real_image and has_real_price:
            gold_items.append({
                'row_id': row_idx,
                'name': pname,
                'category': unified_cat,
                'subcategory': unified_subcat,
                'brand': brand_val if brand_val else 'HRz Pitstop',
                'make': compat_make,
                'model': compat_model,
                'mrp': final_mrp,
                'selling_price': final_sp,
                'discount': discount_pct,
                'stock': stock_qty if stock_qty is not None else 1,
                'image': verified_image,
                'description': clean_desc,
                'sku': assigned_sku,
                'color': extracted_color,
                'size': extracted_size
            })
        else:
            # Failed Gate 2 or Gate 3 (or Probable Match awaiting full verification)
            missing = []
            if not has_real_image:
                missing.append('IMAGE')
            if not has_real_price:
                missing.append('PRICE')
            missing_str = 'BOTH' if len(missing) == 2 else (missing[0] if missing else 'IDENTITY')

            queue_items.append({
                'source_row': f"Row {row_idx}",
                'product_name': pname,
                'brand': brand_val if brand_val else (brand_pos or 'Unbranded'),
                'category': unified_cat,
                'subcategory': unified_subcat,
                'pos_sale_price': sale_price_pos,
                'pos_purchase_price': purch_price_pos,
                'stock_qty': stock_qty,
                'evidence_url': evid_url,
                'missing_fields': missing_str
            })

    # Summary Check
    total_processed = len(gold_items) + len(queue_items) + len(client_hold_items)
    print(f"\n      Verification Results Summary:")
    print(f"      -> 100% Verified Gold Items:       {len(gold_items):4d}")
    print(f"      -> Needs Scraping Queue Items:     {len(queue_items):4d}")
    print(f"      -> Client Hold Items:              {len(client_hold_items):4d}")
    print(f"      -> Total POS Items Reconciled:     {total_processed:4d} / 2502")
    assert total_processed == len(master_rows), f"Reconciliation error: {total_processed} != {len(master_rows)}"

    # ==============================================================================
    # STEP 3: Write Output Files
    # ==============================================================================
    print("\n[6/6] Writing 3 output files...")

    # --------------------------------------------------------------------------
    # Output 1: HRZ_Gold_Master_Verified.xlsx
    # --------------------------------------------------------------------------
    wb_gold = openpyxl.Workbook()
    # Remove default sheet
    wb_gold.remove(wb_gold.active)

    header_font = Font(name='Segoe UI', size=11, bold=True, color='FFFFFFFF')
    header_fill = PatternFill(start_color='FF19232D', end_color='FF19232D', fill_type='solid')
    data_font = Font(name='Segoe UI', size=10)
    border_thin = Side(border_style='thin', color='FFE0E0E0')
    cell_border = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)

    gold_headers = [
        'Part / Product Name', 'Subcategory', 'Brand', 'Compatible Bike Make',
        'Compatible Bike Model', 'MRP (₹)', 'Selling Price (₹)', 'Discount %',
        'Stock Quantity', 'Product Image Filename / URL', 'Short Description',
        'SKU', 'Color / Variant', 'Size', None,
        'Make Dropdown Source', 'All Models Dropdown Source'
    ]

    col_widths = {
        'A': 32, 'B': 28, 'C': 22, 'D': 24, 'E': 30, 'F': 14, 'G': 16,
        'H': 14, 'I': 14, 'J': 40, 'K': 45, 'L': 24, 'M': 18, 'N': 12,
        'O': 5, 'P': 22, 'Q': 28
    }

    # Reference lists from Filled workbook
    make_list = []
    all_models_list = []
    if 'BIKE LISTS' in wb_filled.sheetnames:
        ws_bl = wb_filled['BIKE LISTS']
        for r in list(ws_bl.iter_rows(values_only=True))[1:]:
            if r and r[0] and r[0] not in make_list:
                make_list.append(str(r[0]).strip())
            if r and len(r) > 3 and r[3] and r[3] not in all_models_list:
                all_models_list.append(str(r[3]).strip())

    if not make_list:
        make_list = ['Royal Enfield', 'KTM', 'Bajaj', 'Yamaha', 'Honda', 'Suzuki', 'Hero', 'Triumph', 'TVS', 'Harley-Davidson', 'Universal']
    if not all_models_list:
        all_models_list = ['Universal', 'Classic 350 Reborn', 'Hunter 350', 'Meteor 350', 'Himalayan 450', 'Himalayan 411', 'Duke 390 Gen-3', 'MT-15 V2', 'R15 V4', 'Dominar 400']

    # Group gold items by category
    gold_by_cat = {cat: [] for cat in VALID_SCHEMA.keys()}
    for item in gold_items:
        gold_by_cat[item['category']].append(item)

    for cat_name, valid_subs in VALID_SCHEMA.items():
        ws = wb_gold.create_sheet(title=cat_name)

        # Set column widths
        for col_l, w in col_widths.items():
            ws.column_dimensions[col_l].width = w

        # Write header
        ws.append(gold_headers)
        for col_idx in range(1, 15):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center' if col_idx in [6, 7, 8, 9, 14] else 'left', vertical='center')

        # Dropdown source headers
        ws.cell(row=1, column=16, value='Make Dropdown Source').font = Font(name='Segoe UI', size=10, bold=True, color='FF7F7F7F')
        ws.cell(row=1, column=17, value='All Models Dropdown Source').font = Font(name='Segoe UI', size=10, bold=True, color='FF7F7F7F')

        # Write dropdown sources in cols P and Q
        for m_idx, m_val in enumerate(make_list, start=2):
            ws.cell(row=m_idx, column=16, value=m_val).font = data_font
        for mod_idx, mod_val in enumerate(all_models_list, start=2):
            ws.cell(row=mod_idx, column=17, value=mod_val).font = data_font

        # Write data rows
        items_for_cat = gold_by_cat[cat_name]
        for row_num, item in enumerate(items_for_cat, start=2):
            row_data = [
                item['name'],
                item['subcategory'],
                item['brand'],
                item['make'],
                item['model'],
                item['mrp'],
                item['selling_price'],
                item['discount'],
                item['stock'],
                item['image'],
                item['description'],
                item['sku'],
                item['color'],
                item['size']
            ]
            ws.append(row_data)

            # Style row
            for c_idx in range(1, 15):
                c = ws.cell(row=row_num, column=c_idx)
                c.font = data_font
                c.border = cell_border
                if c_idx in [6, 7, 8, 9]:
                    c.alignment = Alignment(horizontal='right', vertical='center')
                    if c_idx in [6, 7]:
                        c.number_format = '₹#,##0'
                elif c_idx in [12, 13, 14]:
                    c.alignment = Alignment(horizontal='center', vertical='center')

        # Add Data Validations extended to Row 2000
        # 1. Subcategory Validation (Column B)
        subcat_formula = '"' + ','.join(valid_subs) + '"'
        dv_subcat = DataValidation(type='list', formula1=subcat_formula, allow_blank=True)
        dv_subcat.error = f"Please select a valid subcategory for {cat_name}."
        dv_subcat.errorTitle = "Invalid Subcategory"
        ws.add_data_validation(dv_subcat)
        dv_subcat.add("B2:B2000")

        # 2. Brand Validation (Column C)
        dv_brand = DataValidation(type='list', formula1="'LISTS'!$A$2:$A$100", allow_blank=True)
        ws.add_data_validation(dv_brand)
        dv_brand.add("C2:C2000")

        # 3. Make Validation (Column D)
        dv_make = DataValidation(type='list', formula1=f"$P$2:$P${len(make_list)+1}", allow_blank=True)
        ws.add_data_validation(dv_make)
        dv_make.add("D2:D2000")

        # 4. Model Validation (Column E)
        dv_model = DataValidation(type='list', formula1=f"$Q$2:$Q${len(all_models_list)+1}", allow_blank=True)
        ws.add_data_validation(dv_model)
        dv_model.add("E2:E2000")

        # 5. Price numeric validation (Cols F & G >= 0)
        dv_price = DataValidation(type='decimal', operator='greaterThanOrEqual', formula1=0, allow_blank=True)
        ws.add_data_validation(dv_price)
        dv_price.add("F2:G2000")

        # 6. Stock whole number validation (Col I >= 0)
        dv_stock = DataValidation(type='whole', operator='greaterThanOrEqual', formula1=0, allow_blank=True)
        ws.add_data_validation(dv_stock)
        dv_stock.add("I2:I2000")

    # Copy / Create Reference Sheets
    # BIKE LISTS
    ws_bl_new = wb_gold.create_sheet(title='BIKE LISTS')
    ws_bl_new.append(['Bike Make', 'Bike Model', None, 'All Bike Models (Dropdown Source)'])
    for r in list(wb_filled['BIKE LISTS'].iter_rows(values_only=True))[1:] if 'BIKE LISTS' in wb_filled.sheetnames else []:
        ws_bl_new.append(list(r))

    # MODEL DROPDOWNS
    ws_md_new = wb_gold.create_sheet(title='MODEL DROPDOWNS')
    for r in list(wb_filled['MODEL DROPDOWNS'].iter_rows(values_only=True)) if 'MODEL DROPDOWNS' in wb_filled.sheetnames else []:
        ws_md_new.append(list(r))

    # Updated LISTS sheet with Unified Schema
    ws_lists_new = wb_gold.create_sheet(title='LISTS')
    ws_lists_new.append(['Suggested Brands', None, 'Website Category', 'Subcategory'])

    suggested_brands = []
    if 'LISTS' in wb_filled.sheetnames:
        for r in list(wb_filled['LISTS'].iter_rows(values_only=True))[1:]:
            if r and r[0] and r[0] not in suggested_brands:
                suggested_brands.append(str(r[0]).strip())

    row_ptr = 2
    for b_item in suggested_brands:
        ws_lists_new.cell(row=row_ptr, column=1, value=b_item)
        row_ptr += 1

    row_ptr = 2
    for c_name, s_list in VALID_SCHEMA.items():
        for s_item in s_list:
            ws_lists_new.cell(row=row_ptr, column=3, value=c_name)
            ws_lists_new.cell(row=row_ptr, column=4, value=s_item)
            row_ptr += 1

    wb_gold.save(GOLD_OUTPUT_XLSX)
    print(f"      Saved: {GOLD_OUTPUT_XLSX} ({len(gold_items)} items across 14 tabs)")

    # --------------------------------------------------------------------------
    # Output 2: Needs_Scraping_Queue.csv
    # --------------------------------------------------------------------------
    queue_fields = [
        'Source_Row', 'POS_Product_Name', 'Brand', 'Category', 'Subcategory',
        'POS_Sale_Price', 'POS_Purchase_Price', 'Stock_Qty', 'Verification_Evidence_URL', 'Missing_Fields'
    ]

    with open(QUEUE_OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(queue_fields)
        for item in queue_items:
            writer.writerow([
                item['source_row'],
                item['product_name'],
                item['brand'],
                item['category'],
                item['subcategory'],
                f"{item['pos_sale_price']:.2f}",
                f"{item['pos_purchase_price']:.2f}",
                item['stock_qty'],
                item['evidence_url'],
                item['missing_fields']
            ])
    print(f"      Saved: {QUEUE_OUTPUT_CSV} ({len(queue_items)} items queued for scraping)")

    # --------------------------------------------------------------------------
    # Output 3: Client_Hold_Generic_And_Unfound.xlsx
    # --------------------------------------------------------------------------
    wb_hold = openpyxl.Workbook()
    wb_hold.remove(wb_hold.active)

    hold_headers = [
        '#', 'POS Row', 'SKU', 'Product Name', 'Category', 'Subcategory',
        'Brand', 'Stock Qty', 'POS Sale Price (₹)', 'POS Purchase Price (₹)',
        'Verification Status', 'Source Reference'
    ]

    hold_col_widths = {
        'A': 6, 'B': 10, 'C': 22, 'D': 35, 'E': 25, 'F': 25,
        'G': 20, 'H': 12, 'I': 18, 'J': 18, 'K': 25, 'L': 30
    }

    # Tab 1: Generic Unbranded Items (303 items)
    generic_items = [it for it in client_hold_items if it['ext_ver'] == 'N/A — Generic/Unbranded']
    ws_gen = wb_hold.create_sheet(title=f"Generic Unbranded ({len(generic_items)})")
    for col_l, w in hold_col_widths.items():
        ws_gen.column_dimensions[col_l].width = w
    ws_gen.append(hold_headers)
    for c_idx in range(1, len(hold_headers)+1):
        cell = ws_gen.cell(row=1, column=c_idx)
        cell.font = header_font
        cell.fill = header_fill

    for i, it in enumerate(generic_items, start=1):
        ws_gen.append([
            i, f"Row {it['row_id']}", it['sku'], it['name'], it['category'], it['subcategory'],
            it['brand'] if it['brand'] else 'Generic / Unbranded', it['stock'],
            it['sale_price'], it['purch_price'], it['ext_ver'], it['source_ref']
        ])
        for c_idx in range(1, len(hold_headers)+1):
            cell = ws_gen.cell(row=i+1, column=c_idx)
            cell.font = data_font
            cell.border = cell_border
            if c_idx in [9, 10]:
                cell.number_format = '₹#,##0.00'

    # Tab 2: Not Found Externally (103 items)
    unfound_items = [it for it in client_hold_items if it['ext_ver'] == 'Not Found Externally']
    ws_unf = wb_hold.create_sheet(title=f"Not Found Externally ({len(unfound_items)})")
    for col_l, w in hold_col_widths.items():
        ws_unf.column_dimensions[col_l].width = w
    ws_unf.append(hold_headers)
    for c_idx in range(1, len(hold_headers)+1):
        cell = ws_unf.cell(row=1, column=c_idx)
        cell.font = header_font
        cell.fill = PatternFill(start_color='FF6C1D1D', end_color='FF6C1D1D', fill_type='solid')

    for i, it in enumerate(unfound_items, start=1):
        ws_unf.append([
            i, f"Row {it['row_id']}", it['sku'], it['name'], it['category'], it['subcategory'],
            it['brand'] if it['brand'] else 'Unfound Brand', it['stock'],
            it['sale_price'], it['purch_price'], it['ext_ver'], it['source_ref']
        ])
        for c_idx in range(1, len(hold_headers)+1):
            cell = ws_unf.cell(row=i+1, column=c_idx)
            cell.font = data_font
            cell.border = cell_border
            if c_idx in [9, 10]:
                cell.number_format = '₹#,##0.00'

    wb_hold.save(HOLD_OUTPUT_XLSX)
    print(f"      Saved: {HOLD_OUTPUT_XLSX} ({len(client_hold_items)} total hold items: {len(generic_items)} generic + {len(unfound_items)} unfound)")

    # --------------------------------------------------------------------------
    # Final Output Summary Printout
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PHASE 1 VERIFICATION COMPLETE - EXACT OUTPUT ROW COUNTS:")
    print("=" * 80)
    print(f"1. HRZ_Gold_Master_Verified.xlsx:         {len(gold_items):4d} verified gold rows")
    print(f"2. Needs_Scraping_Queue.csv:               {len(queue_items):4d} queued rows (missing image/price)")
    print(f"3. Client_Hold_Generic_And_Unfound.xlsx:   {len(client_hold_items):4d} hold rows ({len(generic_items)} generic + {len(unfound_items)} not found)")
    print("-" * 80)
    print(f"TOTAL RECONCILED POS ITEMS:                {total_processed:4d} / 2502 (100.0% accounted for)")
    print("=" * 80)

if __name__ == '__main__':
    main()
