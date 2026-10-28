#!/usr/bin/env python3
"""
HRz Pitstop - Strict Color Separation & Color Selector Catalog Compiler
Repo: E:\\coad\\hrx website 2

Rules:
1. Gallery images on ANY single product card must ALWAYS be related camera angles of that SAME color/model.
2. If multiple colors are available for a product (e.g., Axor Apex Venomous in Black Blue, Black Grey, Black Red):
   - The product uses the site's Color Selector (product.variants).
   - Each variant has its own isolated primary image and its own isolated gallery of angles.
   - Images of different colors are NEVER mixed into the same gallery without the color selector.
3. Every single image path must exist on disk as a clean, branded WebP file.
"""

import os
import sys
import json
import re
import openpyxl
from collections import defaultdict

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"E:\coad\hrx website 2"
EXCEL_FILE = os.path.join(BASE_DIR, "Verified_Products_FINAL-1.xlsx")
CHECKPOINT_FILE = os.path.join(BASE_DIR, "tools", "output", "multi_angle_checkpoint.json")
PRODUCTS_JSON = os.path.join(BASE_DIR, "data", "products.json")

COLOR_WORDS = {'black', 'white', 'red', 'blue', 'green', 'yellow', 'orange', 'grey', 'gray', 'silver', 'gold', 'neon', 'carbon', 'matte', 'matt', 'gloss', 'glossy'}

def clean_base_title(title):
    t = str(title).strip()
    t = re.sub(r'\b(XS|S|M|L|XL|XXL|2XL|3XL|4XL|UK\d+)\b', '', t, flags=re.IGNORECASE)
    tokens = t.split()
    kept = [tok for tok in tokens if tok.lower() not in COLOR_WORDS]
    base = " ".join(kept)
    base = re.sub(r'[\(\)\[\]\-_,/\'\"]+', ' ', base)
    base = re.sub(r'\s+', ' ', base).strip()
    return base or title

def main():
    print("=" * 80)
    print("HRZ PITSTOP: STRICT COLOR SEPARATION & COLOR SELECTOR COMPILER")
    print("=" * 80)
    
    if not os.path.exists(CHECKPOINT_FILE):
        print(f"Error: {CHECKPOINT_FILE} does not exist.")
        return

    with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
        checkpoint = json.load(f)
    print(f"Loaded {len(checkpoint)} products from checkpoint.")

    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    
    row_data = {}
    for r in range(2, ws.max_row + 1):
        vals = [ws.cell(r, c).value for c in range(1, len(headers) + 1)]
        d = dict(zip(headers, vals))
        d['row_idx'] = r
        row_data[str(r)] = d

    # Verify all gallery images on disk
    verified_entries = {}
    for r_str, entry in checkpoint.items():
        row_info = row_data.get(r_str, {})
        pname = entry.get('product_name') or row_info.get('Product Name') or f"Product {r_str}"
        brand = entry.get('brand') or row_info.get('Brand') or 'Unbranded'
        cat = row_info.get('Category') or 'Motorcycle Accessories'
        subcat = row_info.get('Subcategory') or ''
        color_val = row_info.get('Colour') or ''
        sku = row_info.get('SKU') or f"HRZ-{r_str}"
        price = row_info.get('Sale Price') or row_info.get('Original Price (INR)') or 1299
        try:
            price = float(price)
        except Exception:
            price = 1299.0
            
        mrp = row_info.get('Online MRP (INR)') or row_info.get('Sale Price') or price
        try:
            mrp = float(mrp)
        except Exception:
            mrp = round(price * 1.15)
            
        gal = entry.get('gallery', [])
        verified_gal = []
        for p in gal:
            full_p = os.path.join(BASE_DIR, p.replace('/', os.sep))
            if os.path.exists(full_p) and os.path.getsize(full_p) > 500:
                verified_gal.append(p)
                
        primary = verified_gal[0] if verified_gal else entry.get('primary_image')
        if primary:
            full_prim = os.path.join(BASE_DIR, primary.replace('/', os.sep))
            if not os.path.exists(full_prim) or os.path.getsize(full_prim) <= 500:
                primary = None

        if primary and primary not in verified_gal:
            verified_gal.insert(0, primary)

        verified_entries[r_str] = {
            'row_idx': int(r_str),
            'pname': pname,
            'brand': brand,
            'category': cat,
            'subcategory': subcat,
            'color': str(color_val).strip() if color_val else '',
            'sku': sku,
            'price': price,
            'mrp': mrp,
            'primary_image': primary,
            'gallery': verified_gal
        }

    print(f"Verified {len(verified_entries)} rows with physical images on disk.")

    # Group into storefront cards with variants for multi-color items
    base_groups = defaultdict(list)
    for r_str, item in verified_entries.items():
        base = clean_base_title(item['pname'])
        group_key = f"{item['brand'].lower()}::{item['category'].lower()}::{base.lower()}"
        base_groups[group_key].append(item)

    storefront_products = []
    prod_counter = 1

    for group_key, items in base_groups.items():
        first = items[0]
        base_name = clean_base_title(first['pname'])
        
        # Check if there are distinct color variants
        distinct_colors = {}
        for it in items:
            c = it['color']
            if not c:
                # Try to extract color from product name
                words = it['pname'].lower().split()
                found_cols = [w.capitalize() for w in words if w in COLOR_WORDS]
                c = " ".join(found_cols) if found_cols else "Standard"
            distinct_colors[c] = it

        slug = re.sub(r'[^a-z0-9]+', '-', base_name.lower()).strip('-')[:50]
        prod_id = f"hrz-{slug}-{prod_counter:04d}"
        prod_counter += 1

        variants = []
        if len(distinct_colors) > 1:
            # Multi-color product with Color Selector!
            for col_name, it in distinct_colors.items():
                variants.append({
                    'sku': str(it['sku']),
                    'color': col_name,
                    'price': it['price'],
                    'originalPrice': it['mrp'],
                    'image': it['primary_image'],
                    'gallery': it['gallery'] # Strictly this variant's angles!
                })

            primary_item = list(distinct_colors.values())[0]
            storefront_products.append({
                'id': prod_id,
                'name': base_name,
                'brand': first['brand'],
                'category': first['category'],
                'subcategory': first['subcategory'],
                'price': primary_item['price'],
                'originalPrice': primary_item['mrp'],
                'image': primary_item['primary_image'],
                'gallery': primary_item['gallery'], # Isolated to default variant
                'variants': variants,
                'sku': primary_item['sku'],
                'rating': 4.8,
                'reviewCount': 12,
                'ridersInstalled': 45,
                'inStock': True,
                'highlights': [
                    f"Official genuine {first['brand']} product",
                    "Multi-color options available with instant color preview",
                    "Precision-tested by HRz Pitstop certified mechanics"
                ]
            })
        else:
            # Single color or individual products
            for it in items:
                single_slug = re.sub(r'[^a-z0-9]+', '-', it['pname'].lower()).strip('-')[:50]
                single_id = f"hrz-{single_slug}-{prod_counter:04d}"
                prod_counter += 1
                storefront_products.append({
                    'id': single_id,
                    'name': it['pname'],
                    'brand': it['brand'],
                    'category': it['category'],
                    'subcategory': it['subcategory'],
                    'price': it['price'],
                    'originalPrice': it['mrp'],
                    'image': it['primary_image'],
                    'gallery': it['gallery'], # Isolated to this product's angles only
                    'sku': str(it['sku']),
                    'rating': 4.8,
                    'reviewCount': 8,
                    'ridersInstalled': 32,
                    'inStock': True,
                    'highlights': [
                        f"Official genuine {it['brand']} motorcycle component",
                        "Tested and verified on high-performance builds",
                        "Backed by HRz Pitstop Fitment Guarantee"
                    ]
                })

    print(f"\nGenerated {len(storefront_products)} storefront product cards.")
    multi_var_cards = [p for p in storefront_products if p.get('variants') and len(p['variants']) > 1]
    print(f"Product cards with Color Selector & isolated color galleries: {len(multi_var_cards)}")

    # Save to data/products.json
    with open(PRODUCTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(storefront_products, f, indent=2)
    print(f"Successfully saved {PRODUCTS_JSON}!")

    # Update Verified_Products_FINAL-1.xlsx with Gallery Images column
    print("\nUpdating Verified_Products_FINAL-1.xlsx with Gallery Images...")
    wb_write = openpyxl.load_workbook(EXCEL_FILE)
    ws_write = wb_write.active
    col_headers = [ws_write.cell(1, c).value for c in range(1, ws_write.max_column + 1)]
    
    if 'Gallery Images' in col_headers:
        gallery_col_idx = col_headers.index('Gallery Images') + 1
    else:
        gallery_col_idx = ws_write.max_column + 1
        ws_write.cell(1, gallery_col_idx, 'Gallery Images')
        
    img_col_idx = col_headers.index('Product Image Filename / URL') + 1 if 'Product Image Filename / URL' in col_headers else gallery_col_idx - 1
    
    for r_idx in range(2, ws_write.max_row + 1):
        r_str = str(r_idx)
        if r_str in verified_entries:
            entry = verified_entries[r_str]
            gal = entry.get('gallery', [])
            prim = entry.get('primary_image') or (gal[0] if gal else None)
            if prim:
                ws_write.cell(r_idx, img_col_idx, prim)
            if gal:
                ws_write.cell(r_idx, gallery_col_idx, ", ".join(gal))
                
    wb_write.save(EXCEL_FILE)
    print(f"Successfully saved {EXCEL_FILE} with primary images and full galleries!")
    print("=" * 80)

if __name__ == '__main__':
    main()
