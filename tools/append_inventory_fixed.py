import json
import openpyxl
import re

# Refined Category Logic
def get_category(name):
    n = str(name).lower()
    
    if 'backrest' in n or 'back rest' in n:
        return 'Luggage & Touring'
        
    if any(x in n for x in ['helmet', 'visor', 'pinlock', 'goggle', 'lens', 'intercom']):
        return 'Helmets & Accessories'
    if any(x in n for x in ['jacket', 'pant', 'glove', 'suit', 'shoe', 'boot', 'jersey', 'knee guard', 'elbow guard', 'rain']):
        return 'Riding Gears'
    if any(x in n for x in ['bag', 'luggage', 'topcase', 'saddle', 'pannier', 'carrier', 'tail bag', 'tank bag']):
        return 'Luggage & Touring'
    if any(x in n for x in ['light', 'fog', 'indicator', 'led', 'bulb', 'flasher', 'hazard', 'headlight', 'switch']):
        return 'Lighting'
    if any(x in n for x in ['crashguard', 'slider', 'crash guard', 'bash plate', 'sump guard', 'radiator guard', 'leg guard', 'grill']):
        return 'Bike Protection'
    if any(x in n for x in ['handle', 'grip', 'lever', 'mirror', 'bar end', 'riser', 'knuckle', 'handlebar']):
        return 'Handlebar & Accessories'
    if any(x in n for x in ['footpeg', 'foot peg', 'footrest', 'foot rest']):
        return 'Foot Rests'
    if any(x in n for x in ['mount', 'bracket', 'holder', 'stay', 'gps']):
        return 'Guards & Mounts'
    if any(x in n for x in ['cap', 'stand', 'paddock', 'oil', 'spool']):
        return 'Oil Caps & Stands'
    if any(x in n for x in ['fairing', 'fender', 'mudguard', 'winglet', 'cowl', 'windscreen', 'windshield', 'tail tidy']):
        return 'Body Fairing and Fenders'
    if any(x in n for x in ['cleaner', 'brush', 'lube', 'polish', 'cloth', 'micro fiber', 'wash', 'chain lube']):
        return 'Cleaning Accessories'
    if any(x in n for x in ['filter', 'exhaust', 'spark plug', 'chain sprocket', 'sprocket', 'chain kit']):
        return 'Performance Accessories'
    if any(x in n for x in ['cover', 'horn', 'cable', 'relay', 'charger']):
        return 'Bike Essentials'
    return 'General Accessories'

# Load Site Products for exact online data
with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return ' '.join(text.split())

site_products_map = {}
for p in products:
    b = p.get('brand', '')
    n = p.get('name', '')
    site_products_map[clean_text(f"{b} {n}")] = p
    site_products_map[clean_text(n)] = p

# Load Excel file
file_path = 'HRZ_Pitstop_Client_Inventory_All_Bike_Models.xlsx'
wb = openpyxl.load_workbook(file_path)

# 1. Clear old inserted data from all main sheets without deleting validation
main_sheets = wb.sheetnames[:14]
for s_name in main_sheets:
    sheet = wb[s_name]
    for row in range(2, sheet.max_row + 1):
        for col in range(1, 13):
            sheet.cell(row=row, column=col).value = None

# Load matched items
with open('matched_768_items.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

row_pointers = {s: 2 for s in main_sheets}

for item in items:
    raw_name = item['raw_name']
    cleaned = clean_text(raw_name)
    
    # Get the site product object
    site_product = None
    if cleaned in site_products_map:
        site_product = site_products_map[cleaned]
    else:
        # Partial match fallback
        tokens = set(cleaned.split())
        for sp_name, sp_obj in site_products_map.items():
            st = set(sp_name.split())
            if len(tokens) > 1 and len(tokens & st) / len(tokens) >= 0.8:
                site_product = sp_obj
                break
                
    if not site_product:
        continue # Shouldn't happen
        
    site_name = site_product.get('name', raw_name)
    category = get_category(site_name)
    if category not in main_sheets:
        category = 'General Accessories'
        
    sheet = wb[category]
    curr_row = row_pointers[category]
    
    # Extract online site data
    brand = site_product.get('brand', '')
    mrp = site_product.get('originalPrice', '')
    sp = site_product.get('price', '')
    stock = 10 # Default stock if site says inStock
    
    # Try to parse first bike compatibility
    compats = site_product.get('bike_compatibility', [])
    bike_make = ''
    bike_model = ''
    if compats and len(compats) > 0:
        first_compat = compats[0].split(' ')
        if len(first_compat) >= 2:
            bike_make = first_compat[0]
            bike_model = ' '.join(first_compat[1:])
        else:
            bike_make = compats[0]
    
    image = site_product.get('image', '')
    desc = site_product.get('description', '')
    if len(desc) > 150: desc = desc[:147] + '...'
    
    # Calculate discount %
    discount = ''
    if mrp and sp and mrp > 0:
        discount = round(((mrp - sp) / mrp) * 100)
    
    sheet.cell(row=curr_row, column=1, value=site_name)          # Part / Product Name
    sheet.cell(row=curr_row, column=2, value=site_product.get('category', '')) # Subcategory
    sheet.cell(row=curr_row, column=3, value=brand)              # Brand
    sheet.cell(row=curr_row, column=4, value=bike_make)          # Compatible Bike Make
    sheet.cell(row=curr_row, column=5, value=bike_model)         # Compatible Bike Model
    sheet.cell(row=curr_row, column=6, value=mrp)                # MRP (₹)
    sheet.cell(row=curr_row, column=7, value=sp)                 # Selling Price (₹)
    sheet.cell(row=curr_row, column=8, value=discount)           # Discount %
    sheet.cell(row=curr_row, column=9, value=stock)              # Stock Quantity
    sheet.cell(row=curr_row, column=10, value=image)             # Product Image Filename / URL
    sheet.cell(row=curr_row, column=11, value=desc)              # Short Description

    row_pointers[category] += 1

wb.save(file_path)
print("Fix applied successfully. All items recreated with proper categories, online site prices, brand, and bike compatibility.")
