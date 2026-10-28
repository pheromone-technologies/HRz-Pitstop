import json
import os
import re
import pandas as pd

def run_remapping():
    print("=== APPLYING ACCURATE CATALOG MAPPINGS FOR GENERIC DUMPS ===")

    with open('data/products.json', encoding='utf-8') as f:
        products = json.load(f)

    targets = ['images/raida/2.webp', 'images/legundary_customs/c.webp', 'images/legundary_customs/d.webp', 'images/vega/4.webp']

    bad_prods = [p for p in products if p.get('image') in targets]
    print(f"Products currently pointing to generic dumps: {len(bad_prods)}")

    # Pre-index all available images in images_processed/catalog
    catalog_files = []
    for dirpath, _, filenames in os.walk('images_processed/catalog'):
        for fn in filenames:
            if fn.lower().endswith('.webp'):
                rel_path = os.path.join(dirpath, fn).replace(os.sep, '/')
                catalog_files.append((fn.lower(), rel_path))

    remapped_count = 0

    for p in bad_prods:
        name = p['name']
        clean_words = [w.lower() for w in re.sub(r'[^a-zA-Z0-9]', ' ', name).split() if len(w) > 2 and w.lower() not in ['and', 'for', 'the', 'with', 'pcs', 'lcb', 'hero', 'tvs']]
        
        best_match = None
        best_score = 0

        for fn_lower, rel_path in catalog_files:
            score = sum(1 for w in clean_words if w in fn_lower)
            # Favor exact word matches
            if score > best_score and score >= 2:
                best_score = score
                best_match = rel_path

        if best_match and best_score >= 2:
            p['image'] = best_match
            p['gallery'] = [best_match]
            print(f"Remapped [{best_score}]: {p['name']} -> {best_match}")
            remapped_count += 1
        else:
            print(f"No strong local match for: {p['name']}")

    print(f"\nTotal remapped from generic dumps: {remapped_count} / {len(bad_prods)}")

    # Save to main products.json
    with open('data/products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    # Save to test design site
    with open('test design site/data/products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    # Save to Final_Master_Catalogue_VERIFIED.xlsx
    df = pd.DataFrame(products)
    df.to_excel('Final_Master_Catalogue_VERIFIED.xlsx', index=False)
    print("Successfully synchronized products.json and Final_Master_Catalogue_VERIFIED.xlsx!")

if __name__ == '__main__':
    run_remapping()
