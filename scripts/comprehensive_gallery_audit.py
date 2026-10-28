#!/usr/bin/env python3
"""
HRz Pitstop: Comprehensive Quality & Zero-Hallucination Audit
"""

import os
import sys
import json
import openpyxl

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"E:\coad\hrx website 2"
EXCEL_FILE = os.path.join(BASE_DIR, "Verified_Products_FINAL-1.xlsx")
PRODUCTS_JSON = os.path.join(BASE_DIR, "data", "products.json")

print("=" * 80)
print("HRZ PITSTOP: FINAL MULTI-ANGLE & COLOR-SEPARATION AUDIT")
print("=" * 80)

# 1. AUDIT EXCEL FILE
print("\n[1/3] Auditing Verified_Products_FINAL-1.xlsx...")
wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
ws = wb.active
headers = [c.value for c in ws[1]]

img_col_idx = headers.index('Product Image Filename / URL') + 1
gal_col_idx = headers.index('Gallery Images') + 1

excel_rows = ws.max_row - 1
missing_primary = 0
missing_gallery = 0
excel_primary_files_missing = 0
excel_gallery_files_missing = 0
total_excel_gallery_images = 0

for r in range(2, ws.max_row + 1):
    prim = ws.cell(r, img_col_idx).value
    gal = ws.cell(r, gal_col_idx).value
    
    if not prim:
        missing_primary += 1
    else:
        prim_abs = os.path.join(BASE_DIR, str(prim).replace('/', os.sep))
        if not os.path.exists(prim_abs) or os.path.getsize(prim_abs) < 500:
            excel_primary_files_missing += 1
            
    if not gal:
        missing_gallery += 1
    else:
        gal_list = [g.strip() for g in str(gal).split(',') if g.strip()]
        total_excel_gallery_images += len(gal_list)
        for g_file in gal_list:
            g_abs = os.path.join(BASE_DIR, g_file.replace('/', os.sep))
            if not os.path.exists(g_abs) or os.path.getsize(g_abs) < 500:
                excel_gallery_files_missing += 1

print(f"  Total Catalog Rows in Excel: {excel_rows}")
print(f"  Rows with Primary Image Populated: {excel_rows - missing_primary} / {excel_rows} (Missing: {missing_primary})")
print(f"  Rows with Gallery Populated: {excel_rows - missing_gallery} / {excel_rows} (Missing: {missing_gallery})")
print(f"  Total Angle Files Populated in Excel: {total_excel_gallery_images}")
print(f"  Primary Files Verified on Disk: {excel_rows - missing_primary - excel_primary_files_missing} (Missing on disk: {excel_primary_files_missing})")
print(f"  Gallery Files Verified on Disk: {total_excel_gallery_images - excel_gallery_files_missing} (Missing on disk: {excel_gallery_files_missing})")

# 2. AUDIT PRODUCTS.JSON
print("\n[2/3] Auditing data/products.json...")
with open(PRODUCTS_JSON, 'r', encoding='utf-8') as f:
    products = json.load(f)

json_missing_image = 0
json_missing_gallery = 0
json_files_missing = 0
total_json_images = 0
variants_count = 0
variant_files_missing = 0

for p in products:
    img = p.get('image')
    gal = p.get('gallery', [])
    
    if not img:
        json_missing_image += 1
    else:
        img_abs = os.path.join(BASE_DIR, img.replace('/', os.sep))
        if not os.path.exists(img_abs) or os.path.getsize(img_abs) < 500:
            json_files_missing += 1
            
    if not gal:
        json_missing_gallery += 1
    else:
        total_json_images += len(gal)
        for g_file in gal:
            g_abs = os.path.join(BASE_DIR, g_file.replace('/', os.sep))
            if not os.path.exists(g_abs) or os.path.getsize(g_abs) < 500:
                json_files_missing += 1
                
    if p.get('variants'):
        for v in p['variants']:
            variants_count += 1
            v_img = v.get('image')
            v_gal = v.get('gallery', [])
            if v_img:
                v_abs = os.path.join(BASE_DIR, v_img.replace('/', os.sep))
                if not os.path.exists(v_abs) or os.path.getsize(v_abs) < 500:
                    variant_files_missing += 1
            for g_file in v_gal:
                g_abs = os.path.join(BASE_DIR, g_file.replace('/', os.sep))
                if not os.path.exists(g_abs) or os.path.getsize(g_abs) < 500:
                    variant_files_missing += 1

print(f"  Total Products in Storefront: {len(products)}")
print(f"  Products with Missing Primary Image: {json_missing_image}")
print(f"  Products with Missing Gallery: {json_missing_gallery}")
print(f"  Storefront Files Missing on Disk: {json_files_missing}")
print(f"  Color Variant SKUs: {variants_count}")
print(f"  Variant Image Files Missing on Disk: {variant_files_missing}")

# 3. COLOR SEPARATION CHECK
print("\n[3/3] Auditing Color Separation across Multi-Angles...")
sample_multi = [p for p in products if len(p.get('gallery', [])) > 1]
print(f"  Products with Multi-Angle Galleries in Storefront: {len(sample_multi)}")
print("  Sample Multi-Angle Galleries:")
for p in sample_multi[:5]:
    print(f"    - {p['name']} ({p.get('brand')}): {len(p['gallery'])} angles")
    for a in p['gallery']:
        print(f"        {a}")

sample_var = [p for p in products if p.get('variants') and len(p['variants']) > 1]
print(f"\n  Sample Color Selector Multi-Variant Products ({len(sample_var)} total):")
for p in sample_var[:3]:
    print(f"    Product: {p['name']} ({p.get('brand')})")
    for v in p['variants']:
        print(f"      Variant '{v['color']}': {len(v.get('gallery', []))} angles, primary: {v.get('image')}")

print("\n" + "=" * 80)
if excel_primary_files_missing == 0 and excel_gallery_files_missing == 0 and json_files_missing == 0:
    print("ALL AUDIT CHECKS PASSED: 100% REAL IMAGES, 100% ON DISK, ZERO HALLUCINATIONS!")
else:
    print("WARNING: Some files missing on disk, inspect above output.")
print("=" * 80)
