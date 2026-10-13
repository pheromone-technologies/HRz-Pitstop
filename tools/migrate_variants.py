import json
import re
from collections import defaultdict
import os

PRODUCTS_FILE = 'data/products.json'
MIGRATED_FILE = 'data/products_migrated.json'

COLOR_REGEX = re.compile(
    r'[-(\s]*\b(Black|Red|Blue|Grey|Green|White|Pink|Brown|Yellow|Orange|Purple|Silver|Gold|Matte Black|Gloss Black|Glossy Black|GreyGreen|Electric Blue|Forest Green|Fluo|Neon|Anthracite|Camo|Desert|Khaki)\b[-)\s]*$', 
    re.IGNORECASE
)

def extract_base_and_color(name):
    # Search for color at the end of the string
    match = COLOR_REGEX.search(name)
    if match:
        color = match.group(1).strip()
        base_name = name[:match.start()].strip()
        # Clean up trailing dashes
        if base_name.endswith('-'):
            base_name = base_name[:-1].strip()
        return base_name, color
    return name.strip(), "Standard"

def main():
    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)

    # Group by (brand, category, base_name)
    groups = defaultdict(list)
    for p in products:
        base_name, color = extract_base_and_color(p['name'])
        key = (p['brand'], p['category'], base_name.lower())
        p['_extracted_color'] = color
        p['_base_name'] = base_name
        groups[key].append(p)

    migrated_products = []
    ambiguous_groups = []
    merged_count = 0

    for key, items in groups.items():
        if len(items) == 1:
            # Single item, just keep its existing variants (which is usually 1)
            # But let's ensure it follows the canonical shape
            p = items[0]
            if not p.get('variants') or len(p['variants']) == 0:
                p['variants'] = [{
                    "color": p['_extracted_color'],
                    "sku": p.get('sku'),
                    "price": p.get('price'),
                    "image": p.get('image'),
                    "gallery": p.get('gallery', [])
                }]
            p['name'] = p['_base_name'] # Rename to base name
            del p['_extracted_color']
            del p['_base_name']
            migrated_products.append(p)
        else:
            # Check for ambiguity: are there duplicate colors?
            colors = [p['_extracted_color'].lower() for p in items]
            if len(colors) != len(set(colors)):
                # Ambiguous: multiple items mapped to same color
                ambiguous_groups.append(key)
                for p in items:
                    del p['_extracted_color']
                    del p['_base_name']
                    migrated_products.append(p)
                continue
            
            # Merge items
            merged_count += 1
            main_product = items[0].copy()
            main_product['name'] = main_product['_base_name']
            
            variants = []
            all_galleries = []
            for p in items:
                v = {
                    "color": p['_extracted_color'],
                    "sku": p.get('sku'),
                    "price": p.get('price'),
                    "image": p.get('image'),
                    "gallery": p.get('gallery', [])
                }
                variants.append(v)
                all_galleries.extend(p.get('gallery', []))
                
            main_product['variants'] = variants
            # Ensure unique gallery images
            main_product['gallery'] = list(dict.fromkeys(all_galleries))
            
            del main_product['_extracted_color']
            del main_product['_base_name']
            migrated_products.append(main_product)

    with open(MIGRATED_FILE, 'w', encoding='utf-8') as f:
        json.dump(migrated_products, f, indent=2)

    print(f"Total original products: {len(products)}")
    print(f"Total migrated products (after merge): {len(migrated_products)}")
    print(f"Number of product groups merged: {merged_count}")
    print(f"Number of ambiguous groups flagged: {len(ambiguous_groups)}")
    
    # Overwrite the original file
    import shutil
    shutil.move(MIGRATED_FILE, PRODUCTS_FILE)

if __name__ == "__main__":
    main()
