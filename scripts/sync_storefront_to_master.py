import openpyxl
import json
import os
import shutil
from collections import Counter

BASE_DIR = r"E:\coad\hrx website 2"
MASTER_XLSX = os.path.join(BASE_DIR, "Final_Master_Catalogue_VERIFIED.xlsx")
PRODUCTS_JSON = os.path.join(BASE_DIR, "data", "products.json")
TEST_PRODUCTS_JSON = os.path.join(BASE_DIR, "test design site", "data", "products.json")
BACKUP_JSON = os.path.join(BASE_DIR, "data", "products.json.bak_master")

# 1. Backup current products.json
shutil.copy2(PRODUCTS_JSON, BACKUP_JSON)
print(f"Backed up {PRODUCTS_JSON} -> {BACKUP_JSON}")

# 2. Load Master Catalogue
wb = openpyxl.load_workbook(MASTER_XLSX, read_only=True)
sheet = wb['Master Catalogue']
headers = next(sheet.iter_rows(values_only=True))

master_by_name = {}
master_by_sku = {}

for row in sheet.iter_rows(values_only=True):
    d = dict(zip(headers, row))
    pname = str(d.get('Product Name') or '').strip().lower()
    sku = str(d.get('SKU') or '').strip()
    cat = str(d.get('Category') or '').strip()
    subcat = str(d.get('Subcategory') or '').strip()
    if pname and cat:
        master_by_name[pname] = (cat, subcat)
    if sku and sku != 'Missing SKU' and cat:
        master_by_sku[sku] = (cat, subcat)
wb.close()

# 3. Load Storefront products.json
with open(PRODUCTS_JSON, 'r', encoding='utf-8') as f:
    products = json.load(f)

before_cats = Counter(p.get('category', '') for p in products)

updated_count = 0
unmatched_count = 0

for p in products:
    pname = p.get('name', '').strip().lower()
    sku = p.get('sku', '').strip()
    
    match = None
    if pname in master_by_name:
        match = master_by_name[pname]
    elif sku in master_by_sku:
        match = master_by_sku[sku]
    else:
        # Check variants
        if 'variants' in p:
            for v in p['variants']:
                vname = str(v.get('name') or '').strip().lower()
                vsku = str(v.get('sku') or '').strip()
                if vname in master_by_name:
                    match = master_by_name[vname]
                    break
                elif vsku in master_by_sku:
                    match = master_by_sku[vsku]
                    break
        if not match:
            # Prefix or substring match
            for m_name, m_val in master_by_name.items():
                if m_name.startswith(pname) or pname.startswith(m_name):
                    match = m_val
                    break
    
    if match:
        new_cat, new_subcat = match
        if new_cat:
            p['category'] = new_cat
        if new_subcat:
            p['subcategory'] = new_subcat
        updated_count += 1
    else:
        unmatched_count += 1

after_cats = Counter(p.get('category', '') for p in products)

# 4. Save updated products.json and sync to test design site
with open(PRODUCTS_JSON, 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)
print(f"Saved updated {PRODUCTS_JSON} ({len(products)} products, {updated_count} synced to master)")

if os.path.exists(os.path.dirname(TEST_PRODUCTS_JSON)):
    with open(TEST_PRODUCTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"Synchronized {TEST_PRODUCTS_JSON}")

print("\n--- Top Categories After Sync ---")
for c, cnt in after_cats.most_common(15):
    print(f"  {c}: {cnt}")
