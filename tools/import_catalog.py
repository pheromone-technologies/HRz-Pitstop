import json
import re
from collections import defaultdict

CATALOG_FILE = r'E:\coad\hrx website 2\catalog.json'
PRODUCTS_FILE = r'E:\coad\hrx website 2\data\products.json'

COLOR_REGEX = re.compile(
    r'[-(\s]*\b(Black|Red|Blue|Grey|Green|White|Pink|Brown|Yellow|Orange|Purple|Silver|Gold|Matte Black|Gloss Black|Glossy Black|GreyGreen|Electric Blue|Forest Green|Fluo|Neon|Anthracite|Camo|Desert|Khaki)\b[-)\s]*$', 
    re.IGNORECASE
)

def extract_base_and_color(name):
    match = COLOR_REGEX.search(name)
    if match:
        color = match.group(1).strip()
        base_name = name[:match.start()].strip()
        if base_name.endswith('-'):
            base_name = base_name[:-1].strip()
        return base_name, color
    return name.strip(), "Standard"

def normalize_category(cat_str):
    if not cat_str: return "Accessories"
    c = cat_str.lower()
    if any(x in c for x in ["helmet"]): return "Helmets"
    if any(x in c for x in ["crash", "guard", "protection", "bash plate", "slider", "tail tidy", "metal visor"]): return "Protection"
    if any(x in c for x in ["light", "fog"]): return "Lights"
    if any(x in c for x in ["luggage", "bag", "carrier", "saddle", "top plate", "rack"]): return "Luggage"
    if any(x in c for x in ["jacket", "glove", "pant", "boot", "goggle", "gear", "suit", "rain"]): return "Riding Gear"
    if any(x in c for x in ["lube", "lubricant", "oil", "maintenance"]): return "Lubricants"
    return "Accessories"

def main():
    with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    # Convert catalog to raw products format
    raw_products = []
    for i, item in enumerate(catalog):
        try:
            price = float(item.get('mrp', 0))
        except:
            price = 0
            
        img_path = item.get('image_path', '')
        if img_path:
            # e.g. images_processed\axor\1.webp -> images_processed/axor/1.webp
            img_path = img_path.replace('\\', '/')
            
        p = {
            "id": f"hrz-prod-cat-{i+1}",
            "name": item.get('product_name', 'Unknown'),
            "brand": item.get('brand', 'Unknown'),
            "category": normalize_category(item.get('category', '')),
            "price": price,
            "originalPrice": int(price * 1.15),
            "image": img_path,
            "gallery": [img_path] if img_path else [],
            "rating": 4.5,
            "authenticity": "100% Genuine",
            "warranty": "12 months",
            "reviewCount": 15,
            "ridersInstalled": 120,
            "badge": "",
            "inStock": True,
            "sku": item.get('sku', f'SKU-{i+1}'),
            "highlights": ["High Quality Material", "100% Genuine Product", "Durable Build"],
            "description": f"Premium quality {item.get('category', 'product')} from {item.get('brand', 'brand')}.",
            "fitmentCategories": ["Adventure", "Roadster", "Classic", "Naked", "Supersport", "Tourer", "Cruiser", "Scrambler", "Twin", "Cafe Racer"],
            "bike_compatibility": item.get('bike_compatibility', []),
            "variants": []
        }
        
        # If catalog explicitly gave a variant that isn't 'Standard', we can use it.
        # But user requested "using the same variant-grouping logic already proven"
        cat_variant = item.get('variant', 'Standard')
        
        base_name, color = extract_base_and_color(p['name'])
        
        # If the regex didn't find a color but catalog has one (e.g. from data structure), use that
        if color == "Standard" and cat_variant != "Standard" and cat_variant:
             color = cat_variant
             
        p['_extracted_color'] = color
        p['_base_name'] = base_name
        raw_products.append(p)

    # Group by (brand, category, base_name)
    groups = defaultdict(list)
    for p in raw_products:
        key = (p['brand'], p['category'], p['_base_name'].lower())
        groups[key].append(p)

    migrated_products = []
    ambiguous_groups = []
    merged_count = 0

    for key, items in groups.items():
        if len(items) == 1:
            p = items[0]
            p['variants'] = [{
                "color": p['_extracted_color'],
                "sku": p.get('sku'),
                "price": p.get('price'),
                "image": p.get('image'),
                "gallery": p.get('gallery', [])
            }]
            p['name'] = p['_base_name']
            del p['_extracted_color']
            del p['_base_name']
            migrated_products.append(p)
        else:
            colors = [p['_extracted_color'].lower() for p in items]
            if len(colors) != len(set(colors)):
                ambiguous_groups.append(key)
                for p in items:
                    del p['_extracted_color']
                    del p['_base_name']
                    migrated_products.append(p)
                continue
            
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
            main_product['gallery'] = list(dict.fromkeys(all_galleries))
            
            del main_product['_extracted_color']
            del main_product['_base_name']
            migrated_products.append(main_product)

    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(migrated_products, f, indent=2)

    print(f"Total catalog items: {len(raw_products)}")
    print(f"Total migrated products (after merge): {len(migrated_products)}")
    print(f"Number of product groups merged: {merged_count}")
    print(f"Number of ambiguous groups flagged: {len(ambiguous_groups)}")

if __name__ == "__main__":
    main()
