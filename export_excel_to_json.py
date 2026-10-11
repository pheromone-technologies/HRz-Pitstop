import openpyxl
import json
import uuid
import os

file_path = 'HRZ_Pitstop_Client_Inventory_All_Bike_Models.xlsx'
wb = openpyxl.load_workbook(file_path, data_only=True)

# Default images by category
fallback_images = {
    'Bike Protection': 'images/crash_guard_product.webp',
    'Handlebar & Accessories': 'images/phone_mount_product.webp',
    'Foot Rests': 'images/bash_plate_product.webp',
    'Guards & Mounts': 'images/crash_guard_product.webp',
    'Oil Caps & Stands': 'images/bash_plate_product.webp',
    'Body Fairing and Fenders': 'images/category_protection.webp',
    'Bike Essentials': 'images/intercom_product.webp',
    'Cleaning Accessories': 'images/bash_plate_product.webp',
    'Performance Accessories': 'images/bash_plate_product.webp',
    'Lighting': 'images/fog_lights_product.webp',
    'Riding Gears': 'images/jacket.webp',
    'Luggage & Touring': 'images/saddlebags_product.webp',
    'Helmets & Accessories': 'images/helmet_product.webp',
    'General Accessories': 'images/phone_mount_product.webp'
}

# Load existing products to preserve stable IDs
existing_by_name = {}
if os.path.exists('data/products.json'):
    try:
        with open('data/products.json', 'r', encoding='utf-8') as f:
            old_prods = json.load(f)
            for p in old_prods:
                existing_by_name[p.get('name', '').strip()] = p
    except Exception as e:
        print("Warning loading existing products.json:", e)

products = []

for sheet_name in wb.sheetnames[:14]:
    sheet = wb[sheet_name]
    for row in range(2, sheet.max_row + 1):
        name = sheet.cell(row=row, column=1).value
        if not name: continue
        name_str = str(name).strip()
        
        sub_cat = sheet.cell(row=row, column=2).value
        brand = sheet.cell(row=row, column=3).value
        bike_make = sheet.cell(row=row, column=4).value
        bike_model = sheet.cell(row=row, column=5).value
        
        mrp = sheet.cell(row=row, column=6).value
        sell_price = sheet.cell(row=row, column=7).value
        stock = sheet.cell(row=row, column=9).value
        image_url = sheet.cell(row=row, column=10).value
        description = sheet.cell(row=row, column=11).value
        
        if not sell_price:
            sell_price = mrp if mrp else 0
        if not mrp:
            mrp = sell_price
            
        try:
            sell_price = float(sell_price)
            mrp = float(mrp)
        except:
            sell_price = 0
            mrp = 0
            
        # Check if product exists to keep ID stable
        existing_p = existing_by_name.get(name_str)
        if existing_p:
            prod_id = existing_p.get('id')
            sku = existing_p.get('sku')
            rating = existing_p.get('rating', 4.8)
            reviewCount = existing_p.get('reviewCount', 12)
            ridersInstalled = existing_p.get('ridersInstalled', 10)
        else:
            unique_id = str(uuid.uuid4())[:8].upper()
            prod_id = "prod-" + unique_id
            sku = "HRZ-" + unique_id
            rating = 4.8
            reviewCount = 12
            ridersInstalled = 10
            
        # Determine Bike Compatibility
        bike_compat = []
        make_clean = str(bike_make or '').strip()
        model_clean = str(bike_model or '').strip()
        
        if make_clean and make_clean != "Universal":
            if model_clean and model_clean != "Universal":
                bike_compat.append(f"{make_clean} {model_clean}")
            else:
                bike_compat.append(make_clean)
        else:
            bike_compat.append("Universal")
            
        # Select best image
        image = fallback_images.get(sheet_name, 'images/bash_plate_product.webp')
        
        # Override image based on subcategory or name if possible
        n = name_str.lower()
        if 'helmet' in n: image = 'images/helmet_product.webp'
        elif 'saddle' in n or 'bag' in n: image = 'images/saddlebags_product.webp'
        elif 'light' in n or 'fog' in n: image = 'images/fog_lights_product.webp'
        elif 'jacket' in n: image = 'images/jacket.webp'
        elif 'glove' in n: image = 'images/gloves.webp'
        elif 'boot' in n: image = 'images/boot.webp'
        
        # USE THE REAL IMAGE FROM EXCEL IF IT EXISTS!
        if image_url and str(image_url).strip() != "":
            image = str(image_url).strip()
            
        prod = {
            "id": prod_id,
            "name": name_str,
            "category": sheet_name,
            "subcategory": str(sub_cat).strip() if sub_cat else "",
            "brand": str(brand).strip() if brand else "HRz Performance",
            "price": sell_price,
            "originalPrice": mrp,
            "image": image,
            "gallery": [image],
            "rating": rating,
            "reviewCount": reviewCount,
            "ridersInstalled": ridersInstalled,
            "inStock": True,
            "sku": sku,
            "bike_compatibility": bike_compat,
            "highlights": [str(description).strip()] if description else []
        }
        
        products.append(prod)

with open('data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2)

print(f"Successfully exported {len(products)} products to data/products.json")
